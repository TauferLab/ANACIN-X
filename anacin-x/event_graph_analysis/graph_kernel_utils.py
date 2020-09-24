
def convert_to_grakel_graph( graph, label_request ):
    """
    Convert an igraph graph object to GraKeL format

    :param graph: The igraph object to convert
    :param label_request: A dict describing which attributes to use as vertex
                          and edge labels respectively
    :returns: A list of items satisfying GraKeL's graph format
    :raises: 
    """
  
    if label_request is not None and label_request["vertex"] == "logical_tick":
        graph = add_logical_tick_labels(graph)

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





def preprocess( graphs, base_kernel_defs, kernels, labelings ):
    labeling_to_graphs =  { "unlabeled" : [ convert_to_grakel_graph(g, None) for g in graphs ] }
    # First check if we need labels at all
    need_labels = False
    for k in kernels:
        constraints = base_kernel_defs[k]["constraints"]
        if constraints["vertex_label"] == "needs":
            need_labels = True
            break
    if not need_labels:
        return labeling_to_graphs
    else:
        for lab in labelings:
            key = (lab["vertex"], lab["edge"])
            labeling_to_graphs[key] = [ convert_to_grakel_graph(g, lab) for g in graphs ]
        return labeling_to_graphs
            
    


    ## First determine if we need to add logical tick labels.
    ## TODO: Move this functionality into dumpi_to_graph
    #graphs = [ add_logical_tick_labels(g) for g in graphs ]
    #
    ## Create mapping between labelings and sets of correspondingly labeled graphs
    #labeling_to_graphs = { l:[ convert_to_grakel_graph(g, l) for g in graphs ] for l in labelings }

    #return labeling_to_graphs

        

