import igraph 
import numpy as np
from utilities import timer
import pprint

legal_vertex_labels = [ "event_type", 
                        "logical_time", 
                        "wall_time", 
                        "callstack",
                        "process_id"
                      ]



def get_edge_latency( graph, edge, clock ):
    """
    """

    vertex_attribute = clock + "_time"
    src_vertex_timestamp = graph.vs[ edge.source ][ vertex_attribute ]
    dst_vertex_timestamp = graph.vs[ edge.target ][ vertex_attribute ]
    return dst_vertex_timestamp - src_vertex_timestamp

def convert_to_grakel_graph( graph, label_request ):
    """
    Convert an igraph graph object to GraKeL format

    :param graph: The igraph object to convert
    :param label_request: A dict describing which attributes to use as vertex
                          and edge labels respectively
    :returns: A list of items satisfying GraKeL's graph format
    :raises: 
    """
    
    # Set edge list
    edge_list = []
    for e in graph.es[:]:
        edge_list.append( ( e.source, e.target ) )
    
    # Set vertex labels if requested
    vid_to_label = {}
    if label_request is not None:
        for v in graph.vs[:]:
            if label_request["vertex"] is not None:
                # If the requested label is a vertex attribute, apply it
                try:
                    vid_to_label[ v.index ] = v[label_request["vertex"]]
                # If it's not a vertex attribute, just apply a dummy label
                except:
                    print("Vertex label: {} not available".format(label_request["vertex"]))
                    vid_to_label[ v.index ] = 0
    
    # Set edge labels if requested
    eid_to_label = {}
    if label_request is not None:
        for e in graph.es[:]:
            if label_request["edge"] is not None:
                # If the requested label is an edge attribute, apply it
                try:
                    eid_to_label[ e.index ] = e[label_request["edge"]]
                # If it's not an existing edge attribute, compute it if possible,
                # or if not, just apply a dummy label
                except:
                    if label_request["edge"] == "logical_time_latency":
                        eid_to_label[ e.index ] = get_edge_latency( graph, e, clock="logical" )
                    elif label_request["edge"] == "wall_time_latency":
                        eid_to_label[ e.index ] = get_edge_latency( graph, e, clock="wall" )
                    else:
                        eid_to_label[ e.index ] = 0
    
    vid_to_attributes = {}
    eid_to_attributes = {}
    
    return [ edge_list, vid_to_label, eid_to_label ]


def add_logical_tick_labels(graph):
    for v in graph.vs[:]:
        preds = v.predecessors()
        if len(preds) > 0:
            pred_logical_times = [ p["logical_time"] for p in preds ]
            tick = max([v["logical_time"] - lts for lts in pred_logical_times])
            v["logical_tick"] = tick
        else:
            v["logical_tick"] = 0
    return graph




def compute_extra_labels( graph ):
    logical_time_increments = [ 0 ] * len(graph.vs[:])
    wall_time_increments = [ 0 ] * len(graph.vs[:])
    for edge in graph.es[:]:
        src_vertex = graph.vs[ edge.source ]
        dst_vertex = graph.vs[ edge.target ]
        # Update logical time increment
        logical_time_increment = dst_vertex["logical_time"] - src_vertex["logical_time"]
        logical_time_increments[ edge.target ] = logical_time_increment
        # Update logical time increment
        wall_time_increment = dst_vertex["wall_time"] - src_vertex["wall_time"]
        wall_time_increments[ edge.target ] = wall_time_increment
    # Add logical time increment vertex label
    graph.vs[:]["logical_tick"] = logical_time_increments
    # Add wall time increment vertex label
    graph.vs[:]["wall_time_increment"] = wall_time_increments
    
    ## Add adjusted logical time 
    #pids = set(graph.vs[:]["process_id"])
    #pid_to_min_lts = { pid:min(graph.vs.select(process_id_eq=pid)[:]["logical_time"]) for pid in pids }
    ##min_lts = min(graph.vs[:]["logical_time"])
    #adjusted_logical_time = [ v["logical_time"] - pid_to_min_lts[v["process_id"]] for v in graph.vs[:] ]
    #graph.vs[:]["adjusted_logical_time"] = adjusted_logical_time
    return graph






def get_relabeled_graphs( graphs, kernels ):
    all_relabeled_graphs = {}
    for kernel in kernels:
        # Which graph kernel are we relabeling for?
        name = kernel[ "name" ]
        # Which label are we using? 
        try:
            label = kernel["params"]["label"]
        except:
            err_msg = "Requested re-labeling for kernel: {} not possible, " \
                      "label not specified".format(name)
            raise KeyError( err_msg )
        # Define a key that uniquely identifies this kernel / label pair
        key = ( name, label )
        # Only generate a relabeled set of graphs if needed
        # The list of kernels may include multiple distinct kernels that can 
        # use the same relabeled graphs (e.g., multiple WL kernels with the same
        # label but different numbers of WL iterations)
        if key not in all_relabeled_graphs:
            # Relabel for Weisfeiler-Lehman Subtree-Pattern kernel 
            if name == "wlst":
                relabeled_graphs = [ relabel_for_wlst_kernel(g, label) for g in graphs ]
            # Relabel for edge-histogram kernel 
            elif name == "eh":
                relabeled_graphs = [ relabel_for_eh_kernel(g, label) for g in graphs ]
            # Relabel for vertex-histogram kernel
            elif name == "vh":
                relabeled_graphs = [ relabel_for_vh_kernel(g, label) for g in graphs ]
            all_relabeled_graphs[ key ] = relabeled_graphs
    return all_relabeled_graphs


"""
Returns a copy of the graph with no vertex or edge labels
"""
def label_free_copy( graph ):
    n_vertices = len(graph.vs[:])
    copy = igraph.Graph(n_vertices, directed=True)
    edges = [ (e.source, e.target) for e in graph.es[:] ]
    copy.add_edges( edges )
    return copy

# Relabels a graph for comparison using the graphkernels Weisfeiler-Lehman 
# Subtree Pattern kernel
#@timer
def relabel_for_wlst_kernel( graph, label="dummy" ):
    # Copy the graph
    n_vertices = len(graph.vs[:])
    relabeled_graph = igraph.Graph(n_vertices, directed=True)
    # If a label was specified, use it. Otherwise, put no label so that the 
    # WL kernel impl. supplies its own labels
    if label == "dummy":
        labels = [ 0 ] * len(graph.vs[:])
    elif label == "random":
        labels = [ np.random.randint(len(graph.vs[:])) ] * len(graph.vs[:])
    else:
        # Weisfeiler-Lehman kernel impl. in graphkernels only accepts 
        # integer-valued labels
        try:
            label_val = int(graph.vs[0][label])
            # Apply labels directly to the copy's vertices
            labels = [ int(label_val) for label_val in graph.vs[:][label] ]
        except:
            # Translate label values of other types to ints first
            label_set = set(graph.vs[:][label])
            label_to_int = { L:I for L,I in zip(label_set,range(len(label_set))) }
            labels = [ label_to_int[label_val] for label_val in graph.vs[:][label] ]
    relabeled_graph.vs[:]["label"] = labels
    # Add edges
    edges = [ (e.source, e.target) for e in graph.es[:] ]
    relabeled_graph.add_edges( edges )
    return relabeled_graph

# Relabels a graph for comparison using the graphkernels edge-histogram kernel
#@timer 
def relabel_for_eh_kernel( graph, label ):
    # Copy the graph
    n_vertices = len(graph.vs[:])
    relabeled_graph = igraph.Graph(n_vertices, directed=True)
    # Add edges 
    edges = [ (e.source, e.target) for e in graph.es[:] ]
    relabeled_graph.add_edges( edges )
    # Add edge labels
    if label == "logical_latency":
        edge_labels = [ graph.vs[e[1]]["logical_time"] - graph.vs[e[0]]["logical_time"] for e in edges ]
        relabeled_graph.es[:][label] = edge_labels
    #FIXME: This crashes graphkernels with a double-free / corruption.
    elif label == "wall_time_latency":
        edge_labels = [ graph.vs[e[1]]["wall_time"] - graph.vs[e[0]]["wall_time"] for e in edges ]
        relabeled_graph.es[:][label] = edge_labels
    else:
        err_str = ( "Unable to relabel for edge histogram kernel using edge "
                    "label: {}".format(label) )
        raise NotImplementedError( err_str )
    return relabeled_graph

"""
Relabels a graph for comparison using the graphkernels vertex-histogram kernel
"""
#@timer
def relabel_for_vh_kernel( graph, label ):
    # Validate requested label
    if label not in legal_vertex_labels:
        err_str = "Vertex label {} is not supported".format( label )
        raise ValueError( err_str )
    # Make a copy of the graph
    relabeled_graph = label_free_copy( graph )
    # Convert string-valued labels into integer valued labels if needed
    if label in [ "event_type", "callstack" ]:
        unique_labels = list(set( graph.vs[:][ label ] ))
        label_to_repr = {}
        for i,l in enumerate(unique_labels):
            label_to_repr[ l ] = i
        labels = [ label_to_repr[l] for l in graph.vs[:][ label ] ]
    else:
        labels = graph.vs[:][ label ]
    # Apply label
    relabeled_graph.vs[:][ label ] = labels
    return relabeled_graph


