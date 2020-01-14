#!/usr/bin/env python3

#SBATCH -N 1
#SBATCH -n 1
#SBATCH -t 01:00:00
#SBATCH -o squash_barriers-%j.out
#SBATCH -e squash_barriers-%j.err

import os
import argparse
import igraph

import pprint

from utilities import ( timer,
                        read_graph
                      )

# Replaces all sequences of consecutive barrier vertices in all program orders
# represented in the input graph with a single barrier vertex
# Example:
# Suppose we have a program order that looks like the following:
# init --> recv --> send --> barrier --> barrier --> recv --> finalize
# The transformed program order will look like:
# init --> recv --> send --> barrier --> recv --> finalize
def squash_barriers( graph ):
    ranks = sorted( list( set( graph.vs[:]["process_id"] ) ) )
    vertices = []
    for rank in ranks:
        event_seq = graph.vs.select( process_id_eq=rank )
        print("Finding consecutive barriers to squash in event sequence for rank: {}".format( rank ))
        for i in range(len(event_seq)):
            v = event_seq[i]
            v_idx = int(v["id"][1:])
            if v["event_type"] == "barrier":
                j = i;
                u = event_seq[j]
                while u["event_type"] == "barrier":
                    j += 1
                    u = event_seq[j]
                last_barrier = event_seq[ j-1 ]
                last_barrier_idx = int( last_barrier["id"][1:] )
                vertices.append( last_barrier )
            else:
                vertices.append( v )
    vertex_ids = [ v["id"] for v in vertices ]
    new_graph = graph.subgraph( vertices, implementation="create_from_scratch" )
    new_edges = []
    for rank in ranks:
        print("Adding program-order edges to re-connect event sequence for rank: {}".format( rank ))
        event_seq = new_graph.vs.select( process_id_eq=rank )
        for i in range(1,len(event_seq)):
            prev_v = event_seq[i-1]
            curr_v = event_seq[i]
            #if prev_v["event_type"] != "init" and prev_v["event_type"] != "finalize":
            if prev_v not in curr_v.predecessors():
                new_edges.append( ( prev_v, curr_v ) )
    new_graph.add_edges( new_edges )
    return new_graph      



def main( graph_path, output_path ):
    # Read in event graph
    graph = read_graph( graph_path )    

    # Generate a new event graph with consecutive barrier nodes merged
    new_graph = squash_barriers( graph ) 

    # If no output path is given, construct default output path
    if output_path is None:
        output_dir = os.path.dirname( graph_path )
        name,ext = os.path.splitext( os.path.basename( graph_path ) )
        output_graph_name = name + "_squashed"
        output_path = output_dir + "/" + output_graph_name + ext

    # Write new graph out to file
    new_graph.write( output_path, format="graphml" )



if __name__ == "__main__":
    desc = "Checks that an event graph is constructed properly"
    parser = argparse.ArgumentParser(description=desc)
    parser.add_argument("graph_path",
                        help="A GraphML file representing the event graph whose consecutive barriers you want to squash")
    parser.add_argument("-o", "--output_path", default=None,
                        action="store", type=str, required=False,
                        help="Path to write transformed graph to. Optional.")
    args = parser.parse_args()

    main( args.graph_path, args.output_path ) 
