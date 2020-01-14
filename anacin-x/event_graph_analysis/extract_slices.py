#!/usr/bin/env python3

#SBATCH -N 1
#SBATCH -n 1
#SBATCH -t 01:00:00
#SBATCH -o extract_slices-%j.out
#SBATCH -e extract_slices-%j.err

import pprint

import argparse
import igraph
import numpy as np
import pathlib
import os
import json

import time

from mpi4py import MPI
comm = MPI.COMM_WORLD

from utilities import timer, read_graph

import sys
sys.path.append(".")
sys.path.append("..")


################################################################################
######################## Slice extraction utilities ############################
################################################################################


# Returns a dict mapping MPI ranks to sequence of barrier vertices
#@timer
def get_rank_to_barrier_seq( graph, slice_ranks ):
    rank_to_barrier_seq = {}
    for rank in slice_ranks:
        barrier_seq = graph.vs.select( process_id_eq=rank, 
                                       event_type_eq="barrier" )
        rank_to_barrier_seq[ rank ] = barrier_seq
    return rank_to_barrier_seq

# Returns a dict mapping MPI ranks to sequences of pairs of subsequent barrier
# vertices
#@timer
def get_rank_to_barrier_pair_seq( rank_to_barrier_seq ):
    rank_to_barrier_pair_seq = {}
    for rank,barrier_seq in rank_to_barrier_seq.items():
        barrier_pair_seq = []
        for i in range(1, len(barrier_seq) ):
            barrier_pair = ( barrier_seq[i-1], barrier_seq[i] )
            barrier_pair_seq.append( barrier_pair )
        rank_to_barrier_pair_seq[ rank ] = barrier_pair_seq
    return rank_to_barrier_pair_seq
            
# Inputs: Dict representing slicing policy and path to parent event graph
# Ouputs: String representing path that slice subgraphs will be written to
# Side Efects: Creates output directory if it doesn't already exist
def make_output_dir( output_dir, slicing_policy, graph_path ):
    graph_dir = os.path.dirname( graph_path )
    # If no user-defined output directory path is provided, construct one based 
    # on the slicing policy
    if output_dir is None:
        output_dir = graph_dir + "/slices_"
        for idx,kvp in enumerate(slicing_policy.items()):
            key,val = kvp
            output_dir += str(key) + "_" + str(val)
            if idx < len(slicing_policy)-1:
                output_dir += "_"
        output_dir += "/"
    else:
        output_dir = graph_dir + "/" + output_dir + "/"

    # If the output directory doesn't exist yet, make it.
    if not os.path.isdir( output_dir ):
        pathlib.Path( output_dir ).mkdir( parents=True, exist_ok=True )
    # Return the output directory so that subsequent slice extraction functions
    # will know where to write the slice subgraphs to
    return output_dir



################################################################################


#@timer
def extract_slice( graph, clock, rank_to_timestamp_interval, include_endpoints ):
    # Get the vertices that are entirely contained within the timestamp bounds
    slice_vertices = get_core_slice_vertices( graph, clock, rank_to_timestamp_interval )
    # If desired, get extra vertices that are not contained within the timestamp
    # bounds, but are an endpoint of an edge whose other endpoint *is* contained
    # within the timestamp bounds
    if include_endpoints:
        endpoint_vertices = get_endpoint_vertices( slice_vertices )
        slice_vertices += endpoint_vertices

    # Actually construct the subgraph. Since the slices will almost always be 
    # very small compared with the parent graph, we force igraph to avoid 
    # copying the parent graph via the implementation parameter.
    slice_subgraph = graph.subgraph( slice_vertices, 
                                     implementation="create_from_scratch")
    return slice_subgraph

#@timer 
def get_core_slice_vertices( graph, clock, rank_to_timestamp_interval ):
    slice_vertices = []
    for rank, timestamp_interval in rank_to_timestamp_interval.items():
        # Unpack interval
        lower_bound, upper_bound = timestamp_interval
        # Accumulate vertices for the current rank (if using logical time)
        if clock == "logical":
            slice_vertices += graph.vs.select( process_id_eq=rank,
                                              logical_time_ge=lower_bound, 
                                              logical_time_le=upper_bound 
                                            )
            slice_vertices += graph.vs.select( process_id_eq=rank,
                                              logical_time_ge=lower_bound, 
                                              logical_time_le=upper_bound, 
                                            )
        # Accumulate vertices for the current rank (if using wall time)
        elif clock == "wall":
            slice_vertices += graph.vs.select( process_id_eq=rank,
                                              wall_time_ge=lower_bound, 
                                              wall_time_le=upper_bound 
                                            )
            slice_vertices += graph.vs.select( process_id_eq=rank,
                                              wall_time_ge=lower_bound, 
                                              wall_time_le=upper_bound, 
                                            )
    return slice_vertices

#@timer
def get_endpoint_vertices( core_slice_vertices ):
    endpoint_vertices = []
    for v in core_slice_vertices:
        for s in v.successors():
            if s["process_id"] != v["process_id"]:
                endpoint_vertices.append(s)
        for p in v.predecessors():
            if ["process_id"] != v["process_id"]:
                endpoint_vertices.append(p)
    return endpoint_vertices

def vertex_pair_to_timestamp_interval( vertex_pair, clock ):
    start_vertex, end_vertex = vertex_pair
    if clock in [ "logical", "wall" ]:
        label = clock + "_time"
        return ( start_vertex[label], end_vertex[label] )
    else:
        raise ValueError("Clock: {} not recognized".format( clock ))

#@timer 
def write_slice( slice_subgraph, output_dir, slice_idx, output_format ):
    output_path = output_dir + "/slice_" + str(slice_idx) + ".graphml"
    slice_subgraph.write( output_path, format=output_format )



def assign_slices( n_slices ):
    my_rank = comm.Get_rank()
    comm_size = comm.Get_size()
    slices_per_rank = n_slices / comm_size
    my_slices = list( filter( lambda x : x % comm_size == my_rank, range( n_slices ) ) )
    #n_assigned_slices = len( my_slices )
    #print("Rank: {}, # slices: {}, indices: {}".format( my_rank, n_assigned_slices, my_slices ))
    return my_slices


#@timer
def extract_barrier_delimited_full_slices( graph, ranks, include_endpoints, output_dir, output_format ):
    # Get a map from MPI ranks to sequences of barrier vertices
    rank_to_barrier_seq = get_rank_to_barrier_seq( graph, ranks )
    # Get a map from MPI ranks to sequences of pairs of subsequent barrier 
    # vertices.
    # Example: Given an MPI rank "r" with an associated barrier sequence 
    # [ b_0, b_1, b_2, ... b_k-1 ], in this map, "r" would map to the sequence
    # [ (b_0, b_1), (b_1, b_2), (b_2, b_3), ... (b_k-2, b_k-1) ]
    rank_to_barrier_pair_seq = get_rank_to_barrier_pair_seq( rank_to_barrier_seq )
    # Get a map from MPI ranks to sequences of pairs of logical timestamps
    # The reason why we do this is that we need to select all of the vertices
    # between a pair of barriers, but that request needs to be phrased in terms 
    # of some predicates on vertex attributes in order to use the select method
    # of an igraph VertexSequence (i.e., to make the slice extraction fast).
    # While in principle we could phrase these predicates in terms of wall-time,
    # logical timestamps for each rank's sequence of vertices are guaranteed to
    # be monotonically increasing, so it is easy to prove that all of the 
    # vertices between the barriers are included. 
    clock = "logical"
    rank_to_timestamp_interval_seq = {}
    for rank,barrier_pair_seq in rank_to_barrier_pair_seq.items():
        timestamp_interval_seq = []
        for idx,barrier_pair in enumerate(barrier_pair_seq):
            timestamp_interval = vertex_pair_to_timestamp_interval( barrier_pair, clock )
            timestamp_interval_seq.append( timestamp_interval )
        rank_to_timestamp_interval_seq[ rank ] = timestamp_interval_seq
    
    n_slices = len( rank_to_timestamp_interval_seq[0] )
    
    assigned_slices = assign_slices( n_slices )

    # Select slice subgraphs based on timestamp bounds 
    #n_slices = len( rank_to_timestamp_interval_seq[0] )
    #for slice_idx in range( n_slices ):
    for slice_idx in assigned_slices:
        # Get the mapping between ranks and timestamp intervals for this slice
        rank_to_timestamp_interval = { rank : seq[ slice_idx ] for rank,seq in rank_to_timestamp_interval_seq.items() }
        # Get the slice subgraph itself
        slice_subgraph = extract_slice( graph, clock, rank_to_timestamp_interval, include_endpoints )
        # Write the slice subgraph to file
        write_slice( slice_subgraph, output_dir, slice_idx, output_format )
        #print("Rank: {} extracted slice: {}".format(my_rank, slice_idx))

################################################################################


#@timer
def get_rank_to_timestamp_interval_seq_fixed_len( rank_to_barrier_seq, clock, slice_len ):
    if clock == "logical":
        timestamp_label = "logical_time"
    elif clock == "wall":
        timestamp_label = "wall_time"
    else:
        raise ValueError("Clock: {} is not supported".format(clock))
    rank_to_timestamp_interval_seq = {}
    for rank, barrier_seq in rank_to_barrier_seq.items():
        timestamp_interval_seq = []
        for barrier_vertex in barrier_seq:
            timestamp_upper_bound = barrier_vertex[ timestamp_label ]
            timestamp_lower_bound = max( timestamp_upper_bound - slice_len, 0 )
            timestamp_interval_seq.append( ( timestamp_lower_bound, timestamp_upper_bound ) )
        rank_to_timestamp_interval_seq[ rank ] = timestamp_interval_seq
    return rank_to_timestamp_interval_seq


#@timer
def extract_barrier_delimited_fixed_len_slices( graph, ranks, include_endpoints, clock, slice_len, output_dir, output_format ):
    # Get a map from MPI ranks to sequences of barrier vertices
    rank_to_barrier_seq = get_rank_to_barrier_seq( graph, ranks )
    # Get a map from MPI ranks to sequences of pairs of timestamps 
    # determined from the timestamp of each barrier and the slice length
    rank_to_timestamp_interval_seq = get_rank_to_timestamp_interval_seq_fixed_len( rank_to_barrier_seq, clock, slice_len )
    # Extract slice subgraphs based on timestamp bounds
    n_slices = len( rank_to_timestamp_interval_seq[0] )
    for slice_idx in range( n_slices ):
        # Get the mapping between ranks and timestamp intervals for this slice
        rank_to_timestamp_interval = { rank : seq[ slice_idx ] for rank,seq in rank_to_timestamp_interval_seq.items() }
        # Get the slice subgraph itself
        slice_subgraph = extract_slice( graph, clock, rank_to_timestamp_interval, include_endpoints )
        
        #n_vertices = len( slice_subgraph.vs[:] )
        #n_edges = len( slice_subgraph.es[:] )
        #print("Extracted slice: {} / {} -- # vertices: {}, # edges: {}".format(slice_idx+1,n_slices,n_vertices,n_edges))

        # Write the slice subgraph to file
        write_slice( slice_subgraph, output_dir, slice_idx, output_format )

################################################################################


### Unvalidated stuff below

#@timer
def extract_barrier_delimited_fixed_size_slices( graph, slice_ranks, vertex_count ):
    rank_to_barrier_seq = get_rank_to_barrier_seq( graph, slice_ranks )
    n_barriers = len( rank_to_barrier_seq[0] )
    
    slice_seq = []

    for idx in range( n_barriers ):
        # Set initial values
        rank_to_slice_vertices = {}
        # Add vertices from delimiting barrier
        for rank in rank_to_barrier_seq:
            rank_to_slice_vertices[ rank ] = [ rank_to_barrier_seq[ rank ][ idx ] ]

        # Start working backwards
        n_vertices = 0
        for vertex_seq in rank_to_slice_vertices.values():
            n_vertices += len( vertex_seq )

        exhausted_ranks = set()
        while n_vertices < vertex_count:

            if exhausted_ranks == set(rank_to_slice_vertices.keys()):
                break

            candidates = {}
            for rank,slice_vertices in rank_to_slice_vertices.items():
                if rank not in exhausted_ranks:
                    earliest_included_vertex = slice_vertices[-1]
                    preds = earliest_included_vertex.predecessors()

                    if len(preds) == 0:
                        exhausted_ranks.add( rank )
                    else:
                        for p in preds:
                            if p["process_id"] == earliest_included_vertex["process_id"]:
                                candidates[ rank ] = p
            
            if len(candidates) == 0:
                break

            # Find the latest candidate
            candidate_rank,latest_candidate = max( candidates.items(), key=lambda x: x[1]["wall_time"] )
            # Include it in the slice
            rank_to_slice_vertices[ candidate_rank ].append( latest_candidate )
            n_vertices += 1


            #for rank,seq in rank_to_slice_vertices.items():
            #    print("Rank: {} --> Seq: {}".format( rank, seq ) )
            #print()
            #print()
        
        all_vertices = []
        for slice_vertices in rank_to_slice_vertices.values():
            all_vertices += slice_vertices

        slice_subgraph = graph.subgraph( all_vertices, implementation="create_from_scratch" )

        #visualize( slice_subgraph )
        #exit()
        slice_seq.append( slice_subgraph )

    return slice_seq


#@timer
def get_wall_time_slice_seq(  graph, time_unit, slice_len, slice_overlap ):
    slice_vertices = []
    slice_idx = 0

    
    all_wall_times = graph.vs[:]["wall_time"] 
    min_wall_time = min( all_wall_times )
    max_wall_time = max( all_wall_times )

    n_ranks = 16
    n_finalize_events = 0
    while True:
        wall_time_lower_bound = slice_idx * slice_len
        wall_time_upper_bound = wall_time_lower_bound + slice_overlap

        if wall_time_lower_bound > max_wall_time:
            break

        slice_vertices = graph.vs.select( wall_time_ge=wall_time_lower_bound,
                                          wall_time_le=wall_time_upper_bound )
        n_vertices = len(slice_vertices)
        slice_idx += 1
        print("Slice Index: {} - Wall-Time Lower Bound: {} -- Wall-Time Upper Bound: {} -- # vertices = {}".format(slice_idx, wall_time_lower_bound, wall_time_upper_bound, n_vertices))
        

#@timer 
def get_logical_time_slice_seq_dense( graph, slice_len, slice_overlap, ranks, include_endpoints ):
    slice_seq = []
    n_procs = len(set(graph.vs[:]["process_id"]))
    n_finalize_vertices_visited = 0
    # Keep track of which slice we're on
    slice_idx = 0
    # Set logical time stamp bounds for first slice
    lts_lower = slice_idx * slice_len
    lts_upper = lts_lower + slice_len
    while n_finalize_vertices_visited < n_procs:
        # Extract slice w/r/t logical timestamp interval
        slice_subgraph = get_slice_logical_timestamp_interval( graph, lts_lower, lts_upper, ranks, include_endpoints )
        # Aggregate to slice sequence
        slice_seq.append( slice_subgraph )
        # update number of finalize vertices accounted for
        n_finalize_vertices_visited += len( slice_subgraph.vs.select( event_type_eq="finalize" ) ) 
        # update timestamp interval
        lts_lower = lts_lower + slice_overlap
        lts_upper = lts_lower + slice_len
    return slice_seq
    



"""
Root MPI process reads in graph and slicing policy, then broadcasts to rest
"""
def ingest_inputs( graph_path, slicing_policy_path ):
    #my_rank = comm.Get_rank()
    #if my_rank == 0:
    #    with open( slicing_policy_path, "r" ) as infile:
    #        slicing_policy = json.load( infile )
    #    graph = read_graph( graph_path )
    #else:
    #    slicing_policy = None
    #    graph = None
    #slicing_policy = comm.bcast( slicing_policy, root=0 )
    #graph = comm.bcast( graph, root=0 )
    with open( slicing_policy_path, "r" ) as infile:
        slicing_policy = json.load( infile )
    graph = read_graph( graph_path )
    return graph, slicing_policy



################################################################################



# Extracts a sequence of subgraphs (referred to herein and elsewhere as "slices")
# from an event graph
def main( graph_path, slicing_policy_path, output_dir, output_format ):

    start_time = time.time()

    #my_rank = comm.Get_rank()
    #if my_rank == 0:
    #    # Read in slicing policy:
    #    with open( slicing_policy_path, "r" ) as infile:
    #        slicing_policy = json.load( infile )
    #    # Read in parent graph
    #    graph = read_graph( graph_path )    
    #else:
    #    slicing_policy = None
    #    graph = None
    #slicing_policy = comm.bcast( slicing_policy, root=0 )
    #graph = comm.bcast( graph, root=0 )

    graph, slicing_policy = ingest_inputs( graph_path, slicing_policy_path )

    end_time = time.time()

    try:
        n_vertices = len(graph.vs[:])
        n_edges = len(graph.es[:])
    except:
        n_vertices = 0
        n_edges = 0
    print( "Rank: {}, ingestion time: {}, # vertices: {}, # edges: {}".format( my_rank, end_time - start_time, n_vertices, n_edges ))
    comm.barrier()
    exit()
    
    # Determine, and if necessary, create output directory
    output_dir = make_output_dir( output_dir, slicing_policy, graph_path )

    #print("Rank: {} - Output Directory: {}".format( my_rank, output_dir ))

    # Check that output format is in the supported set
    allowed_formats = [ "adjacency", "dimacs", "dot", "graphviz", "edgelist", 
                        "edges", "edge", "gml", "graphml", "graphmlz", "gw",
                        "leda", "lgr", "lgl", "ncol", "net", "pajek", "pickle",
                        "picklez", "svg" ]
    if output_format not in allowed_formats:
        raise ValueError( "Output format: {} not allowed".format( output_format ) )

    # Unless a subset of ranks was passed as a command-line argument, we 
    # slice over all ranks in the event graph
    if slicing_policy["ranks"] == "all":
        ranks = [ int(x) for x in set( graph.vs[:]["process_id"] ) ]
    else:
        ranks = slicing_policy["ranks"]

    # Set whether we're including endpoints of messages that are only partially
    # included within a slice. A value for this needs to be set in any slicing
    # policy so we get it here as opposed to in one of the conditionals below
    include_endpoints = slicing_policy["include_endpoints"]

    ############################################################################
    ################ Extract slices based on slicing policy ####################
    ############################################################################

    # Extract the full subgraphs between pairs of barriers
    if slicing_policy["policy"] == "barrier_delimited_full":
        extract_barrier_delimited_full_slices( graph, ranks, include_endpoints, 
                                               output_dir, output_format )
    
    # Extract subgraphs delimited on one end by a barrier and consisting of all
    # vertices later than a fixed amount of time prior to the barrier
    elif slicing_policy["policy"] == "barrier_delimited_fixed_len":
        clock = slicing_policy["clock"]
        slice_len = slicing_policy["slice_len"]
        extract_barrier_delimited_fixed_len_slices( graph, 
                                                    ranks, 
                                                    include_endpoints, 
                                                    clock,
                                                    slice_len, 
                                                    output_dir, 
                                                    output_format )

    # Extract subgraphs delimited on one end by a barrier and consisting of a 
    # fixed number of vertices. 
    elif slicing_policy["policy"] == "barrier_delimited_fixed_size_num_vertices":
        n_vertices = slicing_policy["slice_size_vertices"]
        extract_barrier_delimited_fixed_size_slices( graph, ranks, n_vertices )
    
        
        
    elif slicing_policy["policy"] == "wall_time":
        time_unit = slicing_policy["time_unit"]
        slice_len = slicing_policy["slice_len"]
        slice_overlap = slicing_policy["slice_overlap"]
        slice_seq = get_wall_time_slice_seq( graph, time_unit, slice_len, slice_overlap )

    elif slicing_policy["policy"] == "logical_time_dense":
        slice_len = slicing_policy["slice_len"]
        slice_overlap = slicing_policy["slice_overlap"]
        slice_seq = get_logical_time_slice_seq_dense( graph, slice_len, slice_overlap, ranks, include_endpoints )

                               

if __name__ == "__main__":
    desc = ""
    parser = argparse.ArgumentParser(description=desc)
    parser.add_argument("graph_path",
                        help="Path to a GraphML file representing an event graph")
    parser.add_argument("slicing_policy",
                        help="Path to a JSON file describing how to slice the event graph")
    parser.add_argument("-o", "--output_dir", default=None,
                        action="store", type=str, required=False,
                        help="Directory to write slices to. Optional.")
    parser.add_argument("-f", "--output_format",
                        action="store", type=str, default="graphml", required=False,
                        help="Format to write slices as. Optional. Default: graphml")

    args = parser.parse_args()
   
    my_rank = comm.Get_rank()
    start_time = time.time()
    
    main( args.graph_path, args.slicing_policy, args.output_dir, args.output_format )
    
    end_time = time.time()
    elapsed = end_time - start_time
    if my_rank == 0:
        print("Total elapsed time: {}".format( elapsed ))



