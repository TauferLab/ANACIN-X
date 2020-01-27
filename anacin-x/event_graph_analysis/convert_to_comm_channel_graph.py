#!/usr/bin/env python3

import igraph
import hashlib
import pygraphviz as pgv

import pprint

def get_sender_pid_from_recv( recv_vertex ):
    preds = recv_vertex.predecessors()
    assert( len( preds ) == 2 )
    for p in preds:
        pred_pid = p["process_id"]
        if pred_pid != recv_vertex["process_id"]:
            return pred_pid

def convert( event_graph ):
    edges = event_graph.es[:]
    comm_graph_vertices = set()
    comm_graph_edges = {}
    for e in edges:
        if e["order"] == "message":
            src_pid = event_graph.vs[ e.source ][ "process_id" ]
            dst_pid = event_graph.vs[ e.target ][ "process_id" ]
            comm_graph_vertices.add( src_pid )
            comm_graph_vertices.add( dst_pid )
            comm_graph_edge = ( src_pid, dst_pid )
            if comm_graph_edge not in comm_graph_edges:
                comm_graph_edges[ comm_graph_edge ] = 1
            else:
                comm_graph_edges[ comm_graph_edge ] += 1
    
    # Construct base comm. channel graph
    comm_graph = igraph.Graph( directed=True )
    comm_graph.add_vertices( list(comm_graph_vertices) )
    comm_graph.add_edges( list(comm_graph_edges.keys()) )

    # Add edge weights that quantify communication intensity between each
    # pair of communicating processes
    comm_graph_edge_weights = list(comm_graph_edges.values() )
    comm_graph.es[:]["n_messages"] = comm_graph_edge_weights
    
    # Add vertex labels that summarize messasge delivery order
    comm_graph_vertex_labels = []
    for pid in sorted(comm_graph_vertices):
        # Get the sequence of recvs for the current process
        event_graph_recv_order = event_graph.vs.select( process_id_eq=pid,
                                                        event_type_eq="recv" )
        # Map to a sequence of sender process IDs
        sender_process_ids = [ get_sender_pid_from_recv( recv ) for recv in event_graph_recv_order ]

        # Build up vertex label for current process
        vertex_label = hashlib.sha256()
        vertex_label.update( str(pid).encode('utf-8') )
        for s in sender_process_ids:
            vertex_label.update( str(s).encode('utf-8') )
        #print( "PID: {}, Hash: {}".format( pid, vertex_label.hexdigest() ) )
        comm_graph_vertex_labels.append( vertex_label.hexdigest() )
    comm_graph.vs[:]["message_order_hash"] = comm_graph_vertex_labels
    
    print( comm_graph )
    pprint.pprint( list(comm_graph.vs[:]) )
    pprint.pprint( list(comm_graph.es[:]) )

    return comm_graph

if __name__ == "__main__":
    g = igraph.Graph(directed=True)
    g.add_vertices(16)
    program_order_edges = [ (0,1), (1,2), (2,3), (3,4), 
                            (5,6), (6,7), (7,8), (8,9), (9,10), (10,11),
                            (12,13), (13,14), (14,15) ]
    message_order_edges = [ (0,6), (4,11),
                            (5,13), (7,2), (8,15), (9,3),
                            (12,1), (14,10) ]
    #message_order_edges = [ (0,6), (4,11),
    #                        (5,13), (7,1), (8,15), (9,3),  # Swapped recv order of first two messages received by process 0 --> changes hash for comm graph vertex 0
    #                        (12,2), (14,10) ]
    g.add_edges( program_order_edges )
    g.add_edges( message_order_edges )
    g.vs[:]["process_id"] = [ 0, 0, 0, 0, 0, 
                              1, 1, 1, 1, 1, 1, 1,
                              2, 2, 2, 2 ]
    g.vs[:]["event_type"] = [ "send", "recv", "recv", "recv", "send",
                              "send", "recv", "send", "send", "send", "recv", "recv",
                              "send", "recv", "send", "recv" ]
    g.es[:]["order"] = [ "program" ]*len(program_order_edges) + [ "message" ]*len(message_order_edges)

    cg = convert( g )
    cg.write_dot("comm_graph.dot")
    pgv_graph = pgv.AGraph("comm_graph.dot")
    pgv_graph.layout()
    pgv_graph.draw("comm_graph.svg")
