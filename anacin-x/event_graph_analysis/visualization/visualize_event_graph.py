#!/usr/bin/env python3

import sys
sys.path.append("../")
sys.path.append("./")

import argparse
import igraph

import pprint
import matplotlib
matplotlib.use('TkAgg')
import matplotlib.pyplot as plt
from matplotlib import colors
from matplotlib.patches import Circle
import matplotlib.patches as mpatches
from matplotlib.collections import PatchCollection, LineCollection, CircleCollection

from utilities import ( timer,
                        read_graph
                      )

@timer
def visualize( graph, barrier_adjustment=False ):
    max_lts = max( graph.vs[:]["logical_time"] )
    max_pid = max( graph.vs[:]["process_id"] )
    vertex_size = 0.1

    # Compute x-axis offsets for each process based on LTS of barrier 
    if barrier_adjustment:
        pids = [ int(pid) for pid in  set( graph.vs[:]["process_id"] ) ]
        n_barriers = len( graph.vs.select( process_id_eq=0, event_type_eq="barrier" ) )
        pid_to_barrier_seq = { pid:graph.vs.select(process_id_eq=pid, event_type="barrier") for pid in pids }
        # First, bucket vertices by which barrier pair they're between
        barrier_pair_to_vertices = {}
        for idx in range(1,n_barriers):
            vertices = []
            for pid in pids:
                lts_lower = pid_to_barrier_seq[ pid ][ idx-1 ][ "logical_time" ]
                lts_upper = pid_to_barrier_seq[ pid ][ idx   ][ "logical_time" ]
                vertices += list( graph.vs.select( logical_time_gt=lts_lower,
                                                   logical_time_lt=lts_upper,
                                                   process_id_eq=pid ) )
            barrier_pair_to_vertices[ (idx-1,idx) ] = vertices
        # Now find offset of each vertex w/r/t to the barrier that occurs before it
        vertex_to_offset = {}
        for pid in pids:
            vertex_seq = graph.vs.select( process_id_eq=pid )
            curr_barrier_lts = 0
            barrier_idx = -1 
            for v in vertex_seq:
                if v["event_type"] == "barrier":
                    curr_barrier_lts = v["logical_time"]
                    barrier_idx += 1
                else:
                    vertex_to_offset[ v["id"] ] = ( barrier_idx, v["logical_time"] - curr_barrier_lts )
           
        # Adjust barriers 
        for barrier_idx in range( 1,n_barriers ):
            # Figure out offset for current barrier
            pid_to_barrier_vertex = { pid:barrier_seq[barrier_idx] for pid,barrier_seq in pid_to_barrier_seq.items() }
            pid_to_barrier_lts = { pid : vertex["logical_time"] for pid,vertex in pid_to_barrier_vertex.items() }
            max_barrier_lts = max( pid_to_barrier_lts.values() )
            pid_to_offset = { pid : (max_barrier_lts - lts) + barrier_idx for pid,lts in pid_to_barrier_lts.items() }
            # Apply offset to current barrier vertices
            for pid,barrier_vertex in pid_to_barrier_vertex.items():
                print("Rank: {}, Old barrier time: {}, New barrier time: {}".format( pid, barrier_vertex["logical_time"], barrier_vertex["logical_time"] + pid_to_offset[pid] ) )
                barrier_vertex["logical_time"] += pid_to_offset[ pid ]
        
        # Adjust everything else
        pid_to_barrier_seq = { pid:graph.vs.select(process_id_eq=pid, event_type="barrier") for pid in pids }
        for v in graph.vs[:]:
            if v["event_type"] not in ["barrier", "init"]:
                pid = v["process_id"]
                preceding_barrier_idx,offset = vertex_to_offset[ v["id"] ]
                if preceding_barrier_idx != -1:
                    v["logical_time"] = pid_to_barrier_seq[pid][preceding_barrier_idx]["logical_time"] + offset

        # Finally adjust finalize vertices
        max_lts = max( graph.vs[:]["logical_time"] )
        finalize_vertices = graph.vs.select( event_type_eq="finalize" )
        for v in finalize_vertices:
            v["logical_time"] = max_lts + 1


    barrier_patches = []
    send_patches = []
    recv_patches = []
    misc_patches = []
    for v in graph.vs[:]:
        #if barrier_adjustment:
        #    x_coord = v["logical_time"] + pid_to_offset[ v["process_id"] ]
        #else:
        x_coord = v["logical_time"] 
        y_coord = v["process_id"]
        event_type = v["event_type"]
        if event_type == "barrier":
            patch = Circle( ( x_coord, y_coord ), radius = vertex_size, color = "black" )
            barrier_patches.append( patch ) 
        elif event_type == "send":
            patch = Circle( ( x_coord, y_coord ), radius = vertex_size, color = "blue" )
            send_patches.append( patch ) 
        elif event_type == "recv":
            patch = Circle( ( x_coord, y_coord ), radius = vertex_size, color = "red" )
            recv_patches.append( patch ) 
        else:
            patch = Circle( ( x_coord, y_coord ), radius = vertex_size, color = "green" )
            misc_patches.append( patch ) 

    program_order_lines = []
    message_order_lines = []
    for e in graph.es[:]:
        src_vid = e.source
        dst_vid = e.target
        src_pid = graph.vs[ src_vid ][ "process_id" ]
        dst_pid = graph.vs[ dst_vid ][ "process_id" ]
        #if barrier_adjustment:
        #    src_x = graph.vs[ src_vid ][ "logical_time" ] + pid_to_offset[ src_pid ]
        #else:
        src_x = graph.vs[ src_vid ][ "logical_time" ]
        src_y = graph.vs[ src_vid ][ "process_id" ] 
        #if barrier_adjustment:
        #    dst_x = graph.vs[ dst_vid ][ "logical_time" ] + pid_to_offset[ dst_pid ]
        #else:
        dst_x = graph.vs[ dst_vid ][ "logical_time" ] 
        dst_y = graph.vs[ dst_vid ][ "process_id" ] 
        line = [ ( src_x, src_y ), ( dst_x, dst_y ) ]
        if src_pid == dst_pid:
            program_order_lines.append( line )
        else:
            message_order_lines.append( line )
   
    # Creaet patch collections for each kind of vertex
    barrier_collection = PatchCollection( barrier_patches, facecolor="black", zorder=10 )
    send_collection = PatchCollection( send_patches, facecolor="blue", zorder=10 )
    recv_collection = PatchCollection( recv_patches, facecolor="red", zorder=10 )
    misc_collection = PatchCollection( misc_patches, facecolor="green", zorder=10 )
    
    # Create line collections for each kind of edge
    message_order_edge_collection = LineCollection( message_order_lines, 
                                                    colors="black", 
                                                    linewidth=0.25, 
                                                    linestyle="solid",
                                                    zorder=5
                                                  )

    program_order_edge_collection = LineCollection( program_order_lines, 
                                                    colors="gray", 
                                                    linewidth=0.25, 
                                                    linestyle="dashed",
                                                    zorder=5
                                                  )
    fig, ax = plt.subplots()

    #ax.add_collection( barrier_collection )
    ax.add_collection( send_collection )
    ax.add_collection( recv_collection )
    ax.add_collection( misc_collection )

    ax.add_collection( program_order_edge_collection )
    ax.add_collection( message_order_edge_collection )

    ax.set_aspect("equal")
    ax.autoscale_view()

    plt.show()


def extract_slice( graph, lower_bound, upper_bound, ranks, partials ):
    vertices = []
    if ranks is None:
        vertices += list( graph.vs.select( logical_time_ge=lower_bound,
                                           logical_time_le=upper_bound ) )
    else:
        for rank in ranks:
            vertices += list( graph.vs.select( logical_time_ge=lower_bound,
                                               logical_time_le=upper_bound,
                                               process_id=rank ) )
    if partials:
        endpoints = []
        for vertex in vertices:
            for p in vertex.predecessors():
                if p["process_id"] != vertex["process_id"]:
                    endpoints.append( p )
            for s in vertex.successors():
                if s["process_id"] != vertex["process_id"]:
                    endpoints.append( s )
        vertices += endpoints
    slice_subgraph = graph.subgraph( vertices, implementation="create_from_scratch" )
    return slice_subgraph
        
            

def main( graph_path, barrier_adjustment, take_slice, lower_bound, upper_bound, ranks, partials ):
    graph = read_graph( graph_path )
    if take_slice:
        graph = extract_slice( graph, lower_bound, upper_bound, ranks, partials )
    visualize( graph, barrier_adjustment )
    
if __name__ == "__main__":
    desc = "A script to visualize a pair of event graphs (or slices thereof)"
    parser = argparse.ArgumentParser(description=desc)
    parser.add_argument("graph_path",
                        help="The graph being visualized")
    parser.add_argument("-b", "--barrier_adjustment", action="store_true", default=False,
                        help="Shift vertices so that barriers occur at same logical time across all ranks. Default: False")
    parser.add_argument("-s", "--take_slice", action="store_true", default=False,
                        help="Only visualize a selected slice of the event graph. Default: False")
    parser.add_argument("-l", "--lower_bound", type=int, required=False,
                        help="If visualizing a slice the lower logical timestamp bound")
    parser.add_argument("-u", "--upper_bound", type=int, required=False,
                        help="If visualizing a slice the upper logical timestamp bound")
    parser.add_argument("-r", "--ranks", 
                        nargs="+", type=int, required=False, default=None,
                        help="List of MPI ranks to include in slice. Omitting this parameter includes all ranks.")
    parser.add_argument("-p", "--partials", 
                        action="store_true", default=False,
                        help="Slice will include edges even if only one vertex is within the slice bounds")
    args = parser.parse_args()

    main( args.graph_path, args.barrier_adjustment, args.take_slice, args.lower_bound, args.upper_bound, args.ranks, args.partials )
