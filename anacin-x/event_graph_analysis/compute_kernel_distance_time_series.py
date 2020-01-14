#!/usr/bin/env python3

#SBATCH -t 12:00:00
#SBATCH -o compute_kernel_distance_time_series-%j.out
#SBATCH -e compute_kernel_distance_time_series-%j.err

import argparse
import os 
import glob
import pickle as pkl
import json

import igraph
import graphkernels
import graphkernels.kernels as gk
import numpy as np

import pprint

from mpi4py import MPI
comm = MPI.COMM_WORLD

import sys
sys.path.append(".")

from utilities import ( read_graphs_parallel, 
                        timer, 
                        read_graph,
                        merge_dicts
                      )

from graph_kernel_preprocessing import ( relabel_for_wlst_kernel,
                                         relabel_for_vh_kernel,
                                         relabel_for_eh_kernel
                                       )

from graph_kernel_postprocessing import ( convert_to_distance_matrix,
                                          validate_kernel_matrix
                                        )

################################################################################
############################ Utility functions #################################
################################################################################

#@timer
def get_slice_data( slice_dirs, slice_idx, kernel_params, callstacks_available ):
    #print("Ingesting subgraphs for slice: {}".format( slice_idx ))
    slice_subgraph_paths = [ sd + "/slice_" + str(slice_idx) + ".graphml" for sd in slice_dirs ]
    #slice_subgraphs = read_graphs_parallel( slice_subgraph_paths )
    slice_subgraphs = [ read_graph(g) for g in slice_subgraph_paths ]
    
    # Compute the requested kernel distance matrices
    #print("Computing kernel distances for slice: {}".format( slice_idx ))
    kernel_distance_data = compute_kernel_distance_matrices( slice_subgraphs, 
                                                             kernel_params )
    
    # Extract wall-time information for correlating with application events
    #print("Extracting wall-time data for slice: {}".format( slice_idx ))
    wall_time_data = extract_wall_time_data( slice_subgraphs )
    
    # Extract callstack data if available
    if callstacks_available:
        #print("Extracting callstack data for slice: {}".format( slice_idx ))
        callstack_data = extract_callstack_data( slice_subgraphs )
    else:
        callstack_data = {}
    
    slice_data = { "kernel_distance" : kernel_distance_data,
                   "wall_time"       : wall_time_data,
                   "callstack"       : callstack_data }
    return slice_data


#@timer
def get_all_trace_dirs( traces_root_dir, 
                        runs, 
                        run_range_lower, 
                        run_range_upper ):
    all_trace_dirs = glob.glob( traces_root_dir + "/run*/" )
    all_trace_dirs = sorted( all_trace_dirs, key=lambda x: int(x.split("/")[-2][3:]) )
    if run_range_lower is not None and run_range_upper is not None:
        trace_dirs = all_trace_dirs[run_range_lower-1 : run_range_upper]
    else:   
        trace_dirs = all_trace_dirs
    return trace_dirs


#@timer
def get_slice_dirs( trace_dirs, slicing_policy ):
    trace_dir_to_slice_dir = {}
    for td in trace_dirs:
        slice_dir = td + "/slices_"
        for idx,kvp in enumerate(slicing_policy.items()):
            key,val = kvp
            slice_dir += str(key) + "_" + str(val)
            if idx < len(slicing_policy)-1:
                slice_dir += "_"
        slice_dir += "/"
        trace_dir_to_slice_dir[ td ] = slice_dir
    return trace_dir_to_slice_dir


#@timer 
def make_output_path( traces_root_dir, slicing_policy, kernel_params ):
    output_path = traces_root_dir + "/kernel_distance_time_series_"
    output_path += "SLICING_"
    for idx,kvp in enumerate( sorted(slicing_policy.items()) ):
        k,v = kvp
        output_path += str(k) + "_" + str(v)
        if idx != len( slicing_policy.items() ) - 1:
            output_path += "_"
    output_path += "_KERNELS_"
    for idx,kernel in enumerate( kernel_params ):
        output_path += "kernel_" + kernel["name"] + "_params_"
        for param_name, param_val in sorted( kernel["params"].items() ):
            output_path += str(param_name) + "_"
            output_path += str(param_val)
        if idx != len(kernel_params)-1:
            output_path += "_"
    output_path += ".pkl"
    return output_path

#@timer
def validate_slice_dirs( slice_dirs ):
    slice_counts = set()
    for sd in slice_dirs:
        slice_files = glob.glob( sd + "/*.graphml" )
        n_slices = len(slice_files)
        slice_counts.add( n_slices )
    assert( len(slice_counts) == 1 )

################################################################################
############### Supplemental slice data extraction functions ###################
################################################################################

#@timer
def extract_wall_time_data( slice_subgraphs ):
    graph_to_wall_time_data = {}
    for idx,g in enumerate(slice_subgraphs):
        wall_times = [ float(wt) for wt in g.vs[:]["wall_time"] ]
        time_stats = {}
        time_stats["median_wall_time"] = np.median( wall_times )
        time_stats["mean_wall_time"] = np.mean( wall_times )
        time_stats["min_wall_time"] = min( wall_times )
        time_stats["max_wall_time"] = max( wall_times )
        graph_to_wall_time_data[idx] = time_stats
    return graph_to_wall_time_data

#@timer
def extract_callstack_data( slice_subgraphs ):
    graph_to_callstack_data = {}
    for idx,g in enumerate(slice_subgraphs):
        callstack_to_count = {}
        callstacks = g.vs[:]["callstack"]
        for c in callstacks:
            if c != "":
                if c not in callstack_to_count:
                    callstack_to_count[c] = 1
                else:
                    callstack_to_count[c] += 1
        graph_to_callstack_data[ idx ] = callstack_to_count
    return graph_to_callstack_data

################################################################################
##################### Graph kernel distance functions ##########################
################################################################################

#@timer 
def compute_kernel_distance_matrices( slice_subgraphs, kernel_params ):
    # Relabel based on requested graph kernels
    kernel_label_pair_to_relabeled_graphs = {}
    for kernel in kernel_params:
        # Which graph kernel are we relabeling for?
        kernel_name = kernel[ "name" ]

        # Which label are we using? 
        try:
            label = kernel["params"]["label"]
        except:
            raise KeyError("Requested re-labeling for kernel: {} not possible, label not specified".format(kernel_name))

        key = ( kernel_name, label )
        if key not in kernel_label_pair_to_relabeled_graphs:
            # Relabel for Weisfeiler-Lehman Subtree-Pattern kernel 
            if kernel_name == "wlst":
                graphs = [ relabel_for_wlst_kernel(g, label) for g in slice_subgraphs ]
            # Relabel for edge-histogram kernel 
            elif kernel_name == "eh":
                graphs = [ relabel_for_eh_kernel(g, label) for g in slice_subgraphs ]
            # Relabel for vertex-histogram kernel
            elif kernel_name == "vh":
                graphs = [ relabel_for_vh_kernel(g, label) for g in slice_subgraphs ]
            kernel_label_pair_to_relabeled_graphs[ key ] = graphs


    # Actually compute the kernel distance matrices
    kernel_to_distance_matrix = {}
    for kp in kernel_params:
        kernel = kp["name"]
        params = kp["params"]
        # Compute Weisfeiler-Lehman subtree pattern kernel
        if kernel == "wlst":
            n_iters = params["n_iters"]
            label   = params["label"]
            kernel_label_pair = ( kernel, label )
            relabeled_graphs = kernel_label_pair_to_relabeled_graphs[ kernel_label_pair ]
            kernel_mat = gk.CalculateWLKernel( relabeled_graphs, n_iters )
            distance_mat = convert_to_distance_matrix( kernel_mat )
            kernel_params_key = ( kernel, label, n_iters )
            kernel_to_distance_matrix[ kernel_params_key ] = distance_mat
        # Compute edge-histogram kernel
        elif kernel == "eh":
            label = params["label"]
            kernel_label_pair = ( kernel, label )
            relabeled_graphs = kernel_label_pair_to_relabeled_graphs[ kernel_label_pair ]
            kernel_mat = gk.CalculateEdgeHistKernel( relabeled_graphs )
            distance_mat = convert_to_distance_matrix( kernel_mat )
            kernel_key = ( kernel, label )
            kernel_to_distance_matrix[ kernel_key ] = distance_mat
        # Compute vertex-histogram kernel
        elif kernel == "vh":
            label = params["label"]
            key = (kernel, label)
            relabeled_graphs = kernel_label_pair_to_relabeled_graphs[ key ]
            kernel_mat = gk.CalculateVertexHistKernel( relabeled_graphs )
            distance_mat = convert_to_distance_matrix( kernel_mat )
            kernel_to_distance_matrix[ key ] = distance_mat
        else:
            raise NotImplementedError("Kernel: {} not supported".format(kernel))
    return kernel_to_distance_matrix
            

################################################################################

def assign_slices( n_slices ):
    my_rank = comm.Get_rank()
    comm_size = comm.Get_size()
    slices_per_rank = n_slices / comm_size
    my_slices = list( filter( lambda x : x % comm_size == my_rank, range( n_slices ) ) )
    return my_slices


def main( traces_root_dir, 
          slicing_policy_path, 
          kernel_file, 
          runs, 
          run_range_lower, 
          run_range_upper, 
          callstacks_available, 
          output_path ):
    
    my_rank = comm.Get_rank()

    if my_rank == 0:

        # Get parent directories for each run. These are the directories that 
        # contain the original DUMPI traces, the full run's event graph, and most
        # importantly the subdirectories of slice subgraphs
        trace_dirs = get_all_trace_dirs( traces_root_dir, 
                                         runs, 
                                         run_range_lower, 
                                         run_range_upper )
            
        # Read in slicing policy
        # This will tell us which sub-directory of the trace directory to look in
        # for the slice subgraph 
        with open( slicing_policy_path, "r" ) as infile:
            slicing_policy = json.load( infile )

        # Determine set of slices to compute over based on slicing policy
        trace_dir_to_slice_dir = get_slice_dirs( trace_dirs, slicing_policy )

        # Sort slice dirs in run order 
        slice_dirs = sorted( trace_dir_to_slice_dir.values(), 
                             key=lambda x:  int(os.path.abspath(x).split("/")[-2][3:]) )

        # Check that each slice directory contains the same number of slice subgraphs
        validate_slice_dirs( slice_dirs )
        
        # Read in kernel parameters
        with open( kernel_file, "r" ) as infile:
            kernel_params = json.load( infile )["kernels"]
    else:
        slicing_policy = None
        slice_dirs = None
        kernel_params = None

    slicing_policy = comm.bcast( slicing_policy, root=0 )
    kernel_params = comm.bcast( kernel_params, root=0 )
    slice_dirs = comm.bcast( slice_dirs, root=0 )

    if my_rank == 0:
        print("Input ingested:")
        print("Slicing Policy:")
        pprint.pprint( slicing_policy )
        print("Graph Kernels:")
        pprint.pprint( kernel_params )
        print("Slice Directories:")
        pprint.pprint( slice_dirs )

    comm.barrier()

    # Compute time series of kernel distance matrices
    slice_idx_to_data = {}
    n_slices = len(glob.glob( slice_dirs[0] + "/*.graphml" ))
    assigned_indices = assign_slices( n_slices )

    comm.barrier()


    #for slice_idx in range( n_slices ):
    for slice_idx in assigned_indices:
        slice_data = get_slice_data( slice_dirs, 
                                     slice_idx, 
                                     kernel_params, 
                                     callstacks_available )
        slice_idx_to_data[ slice_idx ] = slice_data
        print("Rank: {} done computing kernel distance data for slice: {}".format(my_rank, slice_idx))
    
    print("Rank: {} done computing kernel distance data".format(my_rank))
    comm.barrier()

    # Gather all per-slice kernel distance results
    kdts_data = comm.gather( slice_idx_to_data, root=0 )

    if my_rank == 0:
        print("Kernel distance data gathered")

    # Merge on root and write out
    if my_rank == 0:
        kdts = merge_dicts( kdts_data, check_keys=True )

        # Name output path based on slicing policy and kernel params unless one is
        # provided
        if output_path is None:
            output_path = make_output_path( traces_root_dir, 
                                            slicing_policy, 
                                            kernel_params )
        else:
            name,ext = os.path.splitext( output_path )
            if ext != ".pkl":
                output_path = traces_root_dir + "/" + name + ".pkl"
            else:
                output_path = traces_root_dir + "/" + output_path

        # Write out time series data for further analysis or visualization
        with open( output_path, "wb" ) as pklfile:
            #pkl.dump( slice_idx_to_data, pklfile, pkl.HIGHEST_PROTOCOL )
            pkl.dump( kdts, pklfile, pkl.HIGHEST_PROTOCOL )



################################################################################


if __name__ == "__main__":
    desc = ""
    parser = argparse.ArgumentParser(description=desc)
    parser.add_argument("traces_root_dir",
                        help="The top-level directory containing as subdirectories all the traces of the runs for which this kernel distance time series will be computed")  
    parser.add_argument("slicing_policy",
                        help="Path to a JSON file describing how to slice the event graph")
    parser.add_argument("kernel_file", 
                        help="A JSON file describing the graph kernels that will be computed for each set of slice subgraphs")
    parser.add_argument("-c", "--callstacks_available", action="store_true", default=False,
                        help="Toggle on extraction of call-stack data")
    parser.add_argument("-r", "--runs", nargs="+", required=False, default=None,
                        help="Which runs to compute pairwise kernel distances for")
    parser.add_argument("-l", "--run_range_lower", type=int, required=False, default=None,
                        help="lower bound of range of runs")
    parser.add_argument("-u", "--run_range_upper", type=int, required=False, default=None,
                        help="lower bound of range of runs")
    parser.add_argument("-o", "--output_path", default=None,
                        action="store", type=str, required=False,
                        help="Path to write kernel distance time series data to. Optional. If not provided, a default will be constructed from the traces root dir., the slicing policy, and the kernel params.")
    args = parser.parse_args()

    main( args.traces_root_dir, 
          args.slicing_policy, 
          args.kernel_file, 
          args.runs, 
          args.run_range_lower,
          args.run_range_upper,
          args.callstacks_available, 
          args.output_path )


