from functools import wraps
from time import time
import multiprocessing as mp
import psutil
import igraph
import numpy as np

# Silence warnings from igraph
import warnings
warnings.filterwarnings("ignore", module="igraph")

# A simple decorator for timing function calls
def timer(f):
    @wraps(f)
    def wrapper(*args, **kwargs):                                                  
        start = time()                                                             
        result = f(*args, **kwargs)                                                
        end = time()                                                               
        print("{} - Elapsed time: {}".format(f, end-start))
        return result                                                              
    return wrapper

# A function to read in a single graph file via igraph
#@timer
def read_graph( graph_path ):
    graph = igraph.read( graph_path )
    return graph

def read_graphs_serial( graph_paths ):
    return [ read_graph(p) for p in graph_paths ]

def read_graph_task( graph_path ):
    graph = igraph.read( graph_path )
    return (graph_path, graph)

def read_graphs_parallel( graph_paths, return_sorted=False ):
    n_cpus = psutil.cpu_count( logical=True )
    workers = mp.Pool( n_cpus )
    res = workers.map_async( read_graph_task, graph_paths )
    graphs = res.get()
    workers.close()
    if return_sorted:
        return [ g[1] for g in sorted( graphs, key=lambda x : x[0] ) ]
    else:
        return [ g[1] for g in graphs ]


# A function to read in a set of graphs whose paths are listed in a text file
@timer
def read_graphs( graph_list ):
    with open(graph_list, "r") as infile:
        paths = infile.readlines()
        paths = [ p.strip() for p in paths ]
        # Ignore empty lines if they're in the graph list by accident
        paths = list(filter(lambda line: len(line) > 0, paths))
    graphs = []
    for path in paths:
        graph = read_graph( path )
        graphs.append( graph )
    return graphs

def merge_dicts( list_of_dicts, check_keys=False ):
    merged = {}
    if check_keys:
        if not all_unique_keys( list_of_dicts ):
            raise RuntimeError("Duplicate keys present")
    for d in list_of_dicts:
        merged.update( d )
    return merged

def all_unique_keys( list_of_dicts ):
    all_keys = []
    for d in list_of_dicts:
        all_keys += list( d.keys() )
    key_set = set( all_keys )
    if len(key_set) != len(all_keys):
        return False
    else:
        return True
        
