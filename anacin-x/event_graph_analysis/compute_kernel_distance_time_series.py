#!/usr/bin/env python3

#SBATCH -t 12:00:00
#SBATCH -o compute_kernel_distance_time_series-%j.out
#SBATCH -e compute_kernel_distance_time_series-%j.err

import argparse
import os 
import glob
import pickle as pkl
import json
from pathlib import Path

import igraph
import graphkernels
import graphkernels.kernels as gk
import numpy as np

import grakel

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

from graph_kernel_preprocessing import ( get_relabeled_graphs
                                       )

from graph_kernel_postprocessing import ( convert_to_distance_matrix,
                                          validate_kernel_matrix
                                        )

################################################################################
############################ Utility functions #################################
################################################################################

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


################################################################################
##################### Graph kernel distance functions ##########################
################################################################################

#@timer 
def compute_kernel_distance_matrices( slice_subgraphs, kernel_params ):
    # Relabel based on requested graph kernels
    kernel_label_pair_to_relabeled_graphs = get_relabeled_graphs( slice_subgraphs, kernel_params )

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
####################### Slice data extraction functions ########################
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
        mpi_fns = g.vs[:]["mpi_function"]
        for c,f in zip(callstacks, mpi_fns):
            if c != "":
                key = (c,f)
                if key not in callstack_to_count:
                    callstack_to_count[key] = 1
                else:
                    callstack_to_count[key] += 1
        graph_to_callstack_data[ idx ] = callstack_to_count
    return graph_to_callstack_data

#@timer
def get_slice_data( slice_dirs, slice_idx, kernel_params, callstacks_available ):
    print("Ingesting subgraphs for slice: {}".format( slice_idx ))
    slice_subgraph_paths = [ str(sd) + "/slice_" + str(slice_idx) + ".graphml" for sd in slice_dirs ]
    #slice_subgraphs = read_graphs_parallel( slice_subgraph_paths )
    slice_subgraphs = [ read_graph(g) for g in slice_subgraph_paths ]
    
    # Compute the requested kernel distance matrices
    print("Computing kernel distances for slice: {}".format( slice_idx ))
    kernel_distance_data = compute_kernel_distance_matrices( slice_subgraphs, 
                                                             kernel_params )
    
    # Extract wall-time information for correlating with application events
    print("Extracting wall-time data for slice: {}".format( slice_idx ))
    wall_time_data = extract_wall_time_data( slice_subgraphs )
    
    # Extract callstack data if available
    if callstacks_available:
        print("Extracting callstack data for slice: {}".format( slice_idx ))
        callstack_data = extract_callstack_data( slice_subgraphs )
    else:
        callstack_data = {}
    
    slice_data = { "kernel_distance" : kernel_distance_data,
                   "wall_time"       : wall_time_data,
                   "callstack"       : callstack_data }
    
    #for k,d in kernel_distance_data.items():
    #    if np.count_nonzero( d ) > 0:
    #        pprint.pprint( slice_data )
    #        exit()

    return slice_data



################################################################################
######## Functions for dividing computations between available proceses ########
################################################################################

"""
Determines which slice indices each MPI process is responsible for via
round-robin assignment
"""
def assign_slice_indices( n_slices, slices, slice_range_lower, slice_range_upper ):
    rank = comm.Get_rank()
    n_procs = comm.Get_size()
    if slices is not None:
        requested_slices = slices
    elif slices is None and slice_range_lower is not None and slice_range_upper is not None:
        requested_slices = range(slice_range_lower, slice_range_upper )
    else:
        requested_slices = range( n_slices )
    indices = list(filter(lambda x : x % n_procs == rank, range(len(requested_slices))))
    indices = [ requested_slices[idx] for idx in indices ]
    return indices

################################################################################
############### Functions for ingesting and validating inputs ##################
################################################################################

"""
Check that each slice directory has appropriate contents
"""
def validate_slice_dirs( slice_dirs ):
    slice_counts = set()
    for sd in slice_dirs:
        print(sd)
        assert( os.path.isdir(str(sd)) )
        assert( sd.is_dir() )
        slice_counts.add( len(list(sd.glob("*.graphml"))) )
    assert( len( slice_counts ) == 1 )
    return list(slice_counts)[0]

"""
Determines the slice subdirectory's name 
"""
def get_slice_dir_suffix( slicing_policy_file, slice_dir_name ):
    # Case 1: Determine slice directory suffix from slicing policy
    if slicing_policy_file is not None and slice_dir_name is None:
        with open( slicing_policy_file, "r" ) as infile:
            slicing_policy = json.load( infile )
        slice_dir_suffix = "/slices_"
        for idx,kvp in enumerate(slicing_policy.items()):
            key,val = kvp
            slice_dir_suffix += str(key) + "_" + str(val)
            if idx < len(slicing_policy)-1:
                slice_dir_suffix += "_"
        slice_dir_suffix += "/"
    # Case 2: Slice directory suffix provided by user
    elif slicing_policy_file is None and slice_dir_name is not None:
        slice_dir_suffix = "/" + slice_dir_name + "/"
    # Case 3: Neither slicing policy nor user-specified name provided, 
    # use default
    else:
        slice_dir_suffix = "/slices/"
    return slice_dir_suffix

"""
Determines the location of event graph slices
"""
def get_slice_dirs( trace_dirs, slicing_policy, slice_dir_name  ):
    suffix = get_slice_dir_suffix( slicing_policy, slice_dir_name )
    slice_dirs = [ str(td) + suffix for td in trace_dirs ]
    slice_dirs = [ Path(sd) for sd in slice_dirs ]
    return slice_dirs

"""
Determines for which runs' traces to compute the kernel distance time series
"""
def get_requested_trace_dirs( traces_root_dir, runs, run_range_lower, 
                              run_range_upper ):
    # Get all trace directories' paths
    trace_dirs = [ Path(p) for p in glob.glob( traces_root_dir + "/run*/" ) ]
    trace_dirs = sorted( trace_dirs, key=lambda p: p.name )
    # Case 1: Retain only an explicitly specified subset of runs
    if runs is not None:
        requested_trace_dirs = [ trace_dirs[idx-1] for idx in runs ]
    # Case 2: Retain a contiguous range of runs
    elif run_range_lower is not None and run_range_upper is not None:
        run_indices = range( run_range_lower-1, run_range_upper )
        requested_trace_dirs = [ trace_dirs[idx] for idx in run_indices ]
    # Case 3: Retain all runs
    else:
        requested_trace_dirs = trace_dirs
    return requested_trace_dirs

"""
Root MPI process ingests all inputs for later broadcast
"""
def ingest_inputs( traces_root_dir, kernel_file, 
                   runs, run_range_lower, run_range_upper,
                   slicing_policy_file, slice_dir_name ):
    # First determine for which runs we will be computing the kernel distance
    # time series
    trace_dirs = get_requested_trace_dirs( traces_root_dir, runs, 
                                           run_range_lower, run_range_upper )
    # Determine what the subdirectory containing the slices is called
    slice_dirs = get_slice_dirs( trace_dirs, slicing_policy_file, slice_dir_name )
    # Read in file describing all graph kernels to compute and their parameters
    with open( kernel_file, "r" ) as infile:
        kernels = json.load( infile )["kernels"]
    return slice_dirs, kernels    

################################################################################

def main( traces_root_dir, 
          slicing_policy_path, 
          slice_dir_name,
          kernel_file, 
          runs, 
          run_range_lower, 
          run_range_upper, 
          slices, 
          slice_range_lower, 
          slice_range_upper, 
          callstacks_available, 
          output_path ):
    # Get MPI rank
    rank = comm.Get_rank()
    # Ingest inputs on root process
    if rank == 0:
        # Determine slice directories and kernels from inputs
        slice_dirs, kernels = ingest_inputs( traces_root_dir, kernel_file, 
                                             runs, run_range_lower, run_range_upper,
                                             slicing_policy_path, slice_dir_name )

        # Sanity-check the slice directories
        n_slices = validate_slice_dirs( slice_dirs )
        input_config = { "slice_dirs" : slice_dirs,
                         "kernels"    : kernels,
                         "n_slices"   : n_slices }
    else:
        input_config = None
    # Broadcast from root to all other processes
    input_config = comm.bcast( input_config, root=0 )
    # Unpack 
    slice_dirs = input_config["slice_dirs"]
    n_slices   = input_config["n_slices"]
    kernels    = input_config["kernels"]
    
    # Determine slice assignment
    assigned_indices = assign_slice_indices( n_slices, slices, slice_range_lower, slice_range_upper )
    print("Rank: {}, Assigned Slices: {}".format( rank, assigned_indices ))

    # Compute kernel distances and collect wall-time or callstack data as 
    # requested
    slice_idx_to_data = {}
    for slice_idx in assigned_indices:
        slice_data = get_slice_data( slice_dirs, 
                                     slice_idx, 
                                     kernels, 
                                     callstacks_available )
        slice_idx_to_data[ slice_idx ] = slice_data
        print("Rank: {} done computing kernel distance data for slice: {}".format(rank, slice_idx))
    
    comm.barrier()
    print("Rank: {} done computing kernel distance data".format(rank))
    comm.barrier()

    # Gather all per-slice kernel distance results
    kdts_data = comm.gather( slice_idx_to_data, root=0 )

    if rank == 0:
        print("Kernel distance data gathered")

    # Merge on root and write out
    if rank == 0:
        kdts = merge_dicts( kdts_data, check_keys=True )

        # Name output path based on slicing policy and kernel params unless one is
        # provided
        if output_path is None:
            output_path = make_output_path( traces_root_dir, 
                                            slicing_policy, 
                                            kernels )
        else:
            name,ext = os.path.splitext( output_path )
            if ext != ".pkl":
                output_path = traces_root_dir + "/" + name + ".pkl"
            else:
                output_path = traces_root_dir + "/" + output_path

        # Write out time series data for further analysis or visualization
        with open( output_path, "wb" ) as pklfile:
            pkl.dump( kdts, pklfile, pkl.HIGHEST_PROTOCOL )
        print("Kernel distance data written to: {}".format(output_path))



################################################################################


if __name__ == "__main__":
    desc = "Computes a time series of kernel distance distributions for a set of event graphs"
    parser = argparse.ArgumentParser(description=desc)
    parser.add_argument("traces_root_dir",
                        help="The top-level directory containing as subdirectories all the traces of the runs for which this kernel distance time series will be computed")  
    parser.add_argument("kernel_file", 
                        help="A JSON file describing the graph kernels that will be computed for each set of slice subgraphs")
    parser.add_argument("--slicing_policy", required=False, default=None,
                        help="Path to a JSON file describing the slicing policy from which the slices subdirectory may be determined")
    parser.add_argument("--slice_dir_name", required=False, default=None,
                        help="A user-specified name for the slices subdirectory")
    # Indicates whether callstack data should be extracted
    parser.add_argument("-c", "--callstacks_available", action="store_true", default=False,
                        help="Toggle on extraction of call-stack data")
    # Args to select subset of runs
    parser.add_argument("-r", "--runs", nargs="+", required=False, default=None, type=int,
                        help="Which runs to compute pairwise kernel distances for")
    parser.add_argument("-l", "--run_range_lower", type=int, required=False, default=None,
                        help="lower bound of range of runs")
    parser.add_argument("-u", "--run_range_upper", type=int, required=False, default=None,
                        help="lower bound of range of runs")
    # Args to select subset of slices
    parser.add_argument("--slices", nargs="+", required=False, default=None, type=int,
                        help="Which slics to compute pairwise kernel distances for")
    parser.add_argument("--slice_range_lower", type=int, required=False, default=None,
                        help="lower bound of range of slices")
    parser.add_argument("--slice_range_upper", type=int, required=False, default=None,
                        help="lower bound of range of slicds")
    # Defines location of output
    parser.add_argument("-o", "--output_path", default=None,
                        action="store", type=str, required=False,
                        help="Path to write kernel distance time series data to. Optional. If not provided, a default will be constructed from the traces root dir., the slicing policy, and the kernel params.")
    args = parser.parse_args()

    main( args.traces_root_dir, 
          args.slicing_policy, 
          args.slice_dir_name,
          args.kernel_file, 
          args.runs, 
          args.run_range_lower,
          args.run_range_upper,
          args.slices, 
          args.slice_range_lower,
          args.slice_range_upper,
          args.callstacks_available, 
          args.output_path )


