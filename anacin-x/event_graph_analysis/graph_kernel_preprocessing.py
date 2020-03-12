import igraph 

from utilities import timer
import pprint

legal_vertex_labels = [ "event_type", 
                        "logical_time", 
                        "wall_time", 
                        "callstack",
                        "process_id"
                      ]


def convert_to_grakel_graph( graph ):
    edge_list = []
    vid_to_label = {}
    eid_to_label = {}
    for v in graph.vs[:]:
        #vid_to_label[ v.index ] = v["label"]
        vid_to_label[ v.index ] = 0
    for e in graph.es[:]:
        edge_list.append( ( e.source, e.target ) )
    return [ edge_list, vid_to_label, eid_to_label ]


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
def relabel_for_wlst_kernel( graph, label=None ):
    # Copy the graph
    n_vertices = len(graph.vs[:])
    relabeled_graph = igraph.Graph(n_vertices, directed=True)
    # If a label was specified, use it. Otherwise, put no label so that the 
    # WL kernel impl. supplies its own labels
    if label is not None:
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


