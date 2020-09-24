#!/usr/bin/env python3

#SBATCH -o train_regressor_%j.out
#SBATCH -e train_regressor_%j.err
#SBATCH -t 12:00:00

import time
import argparse
import pprint
import glob
import pickle as pkl
import json
import os
import numpy as np

from sklearn.model_selection import train_test_split, KFold
from sklearn import svm
from sklearn.metrics import accuracy_score, mean_squared_error

import sys
sys.path.append(".")
sys.path.append("..")

#from utilities import read_graph, timer
from event_graph_analysis.utilities import read_graph, timer

#from graph_kernel_preprocessing import get_relabeled_graphs, convert_to_grakel_graph
from event_graph_analysis.graph_kernel_preprocessing import get_relabeled_graphs, convert_to_grakel_graph, relabel_for_vh_kernel, relabel_for_wlst_kernel, compute_extra_labels

#from mpi4py import MPI
#comm = MPI.COMM_WORLD

# Suppress sklearn deprecation warning from grakel
import warnings
warnings.simplefilter(action='ignore', category=FutureWarning)

# Import generic GraKeL graph kernel interface
from grakel import GraphKernel

# Import Borgwardt Lab graph kernel implementations
import graphkernels
import graphkernels.kernels as gk

default_base_kernels_path="config/graph_kernels/grakel_base_kernels.json"
default_graph_attributes_path="config/graph_kernels/event_graph_attributes.json"







def get_label( slice_path, nd_fraction_labels ):
    """
    """
    name, ext = os.path.splitext( os.path.basename( slice_path ) ) 
    label_idx = int( name[6:] )
    return nd_fraction_labels[ label_idx ]

def label_slices( traces_root_dir ):
    """
    Associates each event graph slice with a label indicating what fraction of 
    message volume in the communication pattern it models was non-deterministic
    """
    nd_fraction_labels = [ 0, 10, 20, 30, 40, 50, 60, 70, 80, 90, 100 ]
    slice_dirs = glob.glob( traces_root_dir + "/run*/slices/" )
    slice_path_to_label = {}
    for sd in slice_dirs:
        slices = sorted( glob.glob( sd + "/*.graphml" ) )
        for s in slices:
            nd_fraction = get_label( s, nd_fraction_labels )
            slice_path_to_label[ s ] = nd_fraction
    return slice_path_to_label

def load_base_kernel_defs(base_kernels_path=default_base_kernels_path):
    """
    Load GraKeL base graph kernel definitions/parameters from config file
    """
    with open(base_kernels_path, "r") as infile:
        base_kernels = json.load(infile)
    return base_kernels


def get_wl_kernel_defs(base_kernels, wl_iters=10):
    """
    Construct Weisfeiler-Lehman versions of all base kernels
    """
    wl_kernels = {}
    for name,base_kernel in base_kernels.items():
        key = name + "_wl" 
        # Override base kernel's vertex label requirements
        constraints = base_kernel["constraints"]
        constraints["vertex_label"] = "needs"
        base_params = base_kernel["params"]
        wl_kernels[key] = {"constraints" : constraints, "params" : [{"name" : "weisfeiler_lehman", "n_iter" : wl_iters}, base_params]}
    return wl_kernels

def get_hc_kernel_defs(base_kernels):
    """
    Construct Hadamard Code versions of all base kernels
    """
    hadamard_code_kernels = {}
    for name,base_kernel in base_kernels.items():
        key = name + "_hc" 
        # Override base kernel's vertex label requirements
        constraints = base_kernel["constraints"]
        constraints["vertex_label"] = "needs"
        base_params = base_kernel["params"]
        hadamard_code_kernels[key] = {"constraints" : constraints, "params" : [{"name" : "hadamard_code"}, base_params]}
    return hadamard_code_kernels
                   

def get_cf_kernel_defs(base_kernels):
    """
    Construct Core Framework versions of all base kernels
    """
    core_framework_kernels = {}
    for name,base_kernel in base_kernels.items():
        key = name + "_cf" 
        constraints = base_kernel["constraints"]
        base_params = base_kernel["params"]
        core_framework_kernels[key] = {"constraints" : constraints, "params" : [{"name" : "core_framework"}, base_params]}
    return core_framework_kernels



def load_event_graph_attributes(attributes_path=default_graph_attributes_path):
    """
    """
    with open(attributes_path, "r") as infile:
        event_graph_attributes = json.load(infile)
    return event_graph_attributes


@timer
def load_graphs( slice_path_to_label ):
    """
    """
    return [ read_graph(p) for p in sorted(slice_path_to_label) ]

@timer
def convert_graphs( graphs, label_request ):
    """
    """
    return [ convert_to_grakel_graph(g, label_request) for g in graphs ]


@timer
def compute_kernel_matrix( g_train, g_test, graph_kernel ):
    """
    """
    k_train = graph_kernel.fit_transform( g_train )
    k_test  = graph_kernel.transform( g_test )
    return k_train, k_test


@timer
def train_model( k_train, k_test, y_train ):
    """
    :param k_train: The graph kernel matrix computed from the training graphs
    :param k_test: The graph kernel matrix computed from the test graphs
    """
    model = svm.SVR()
    model.fit(k_train, y_train)
    y_pred = model.predict(k_test)
    return y_pred


@timer
def evaluate_kernel( graphs, graph_labels, kernel_def, label_requests, n_folds=10, seed=None ):
    """
    """
    
    # Print progress
    print("Kernel: {}".format(kernel_def))
    
    # Just a few sanity checks
    assert( len(graphs) == len(graph_labels) )

    # Initialize graph kernel
    gk = GraphKernel(kernel=kernel_def, normalize=True)

    # Train kernel on each set of relabeled graphs
    results = []
    for lr in label_requests:
            
        # Print progress
        print("Vertex/Edge Labeling: {}".format(lr))

        # Convert the base graphs into GraKeL-compatible representations with
        # the requested vertex and edge labels, if any.
        relabeled_graphs = convert_graphs( graphs, lr )
        print("# relabeled graphs: {}".format(len(relabeled_graphs)))
       
        # Define lists to track non-determinism fraction prediction results 
        # over multiple folds
        true_nd_vals = []
        pred_nd_vals = []
        mse_vals = []

        # Define training and testing sets
        graph_indices = list(range(len(graph_labels)))
        kf = KFold(n_splits=n_folds, random_state=seed, shuffle=True)
        for split_idx, (train_indices, test_indices) in enumerate(kf.split(graph_indices)):
            
            # Print progress
            print("Running split {}/{}".format(split_idx, n_folds))

            # Get training and testing graphs
            g_train = [ relabeled_graphs[i] for i in train_indices ]
            g_test = [ relabeled_graphs[i] for i in test_indices ]
            print("# training graphs: {}".format(len(g_train)))
            print("# test graphs: {}".format(len(g_test)))

            # Get the non-determinism fraction values for the training and 
            # testing graphs
            y_train = [ graph_labels[i] for i in train_indices ]
            y_test = [ graph_labels[i] for i in test_indices ]

            # Compute the graph kernel matrix
            k_train, k_test = compute_kernel_matrix( g_train, g_test, gk )

            print("K-train shape: {}".format(k_train.shape))
            print("K-test shape: {}".format(k_test.shape))

            # Train SVM regressor using precomputed kernel matrix
            y_pred = train_model( k_train, k_test, y_train )
             
            # Print progress
            print("Done with split {}/{}".format(split_idx, n_folds))
            print()

            # Aggregate results for this fold
            true_nd_vals += list(y_test)
            pred_nd_vals += list(y_pred)
        
        # Aggregate results for this labeling
        results.append( { "true" : true_nd_vals, "pred" : pred_nd_vals } )
    return results



def get_name_from_kernel_def( kernel_def ):
    """
    """
    # Case 1: Base kernel
    if type(kernel_def) == dict:
        return kernel_def["name"]
    # Case 2: Kernel framework (e.g., Weisfeiler-Lehman) + base kernel
    else:
        kernel_framework = kernel_def[0]["name"]
        base_kernel = kernel_def[1]["name"]
        return kernel_framework + "_" + base_kernel


def get_name_from_label_request( label_request ):
    """
    """
    return "vertex_" + str(label_request["vertex"]) + "_edge_" + str(label_request["edge"])




def evaluate_vertex_histogram_kernel( graphs, graph_labels, label_requests, n_folds=10, seed=None ):
    """
    """

    # Print progress
    print("Evaluating Vertex-Histogram Kernel")
    print()
    
    # Just a few sanity checks
    assert( len(graphs) == len(graph_labels) )

    # Mapping from vertex labeling to results
    vertex_labeling_to_results = {}
    
    # Sweep over vertex label options
    for lr in label_requests:
        
        # Unpack
        requested_vertex_label = lr["vertex"]

        # Print progress
        print("Vertex Label: {}".format(requested_vertex_label))
        print()

        # Convert the base graphs into representations with
        # the requested vertex and edge labels, if any.
        relabeled_graphs = [ relabel_for_wlst_kernel(g, label=requested_vertex_label) for g in graphs ]
        
        # Define lists to track non-determinism fraction prediction results 
        # over multiple folds
        true_nd_vals = []
        pred_nd_vals = []
        
        # Compute kernel matrix
        k_mat = gk.CalculateVertexHistKernel( relabeled_graphs )

        # Define training and testing sets
        graph_indices = list(range(len(graph_labels)))
        kf = KFold(n_splits=n_folds, random_state=seed, shuffle=True)
        for split_idx, (train_indices, test_indices) in enumerate(kf.split(graph_indices)):
            
            # Print progress
            print("Running split {}/{}".format(split_idx+1, n_folds))

            # Get training and testing graphs
            g_train = [ relabeled_graphs[i] for i in train_indices ]
            g_test = [ relabeled_graphs[i] for i in test_indices ]

            # Get the non-determinism fraction values for the training and 
            # testing graphs
            y_train = [ graph_labels[i] for i in train_indices ]
            y_test = [ graph_labels[i] for i in test_indices ]

            # Retrieve embeddings of training and test graphs
            k_train = np.zeros((len(train_indices), len(train_indices)))
            k_test  = np.zeros((len(test_indices), len(train_indices)))
            for i in range(len(train_indices)):
                for j in range(len(train_indices)):
                    k_train[i][j] = k_mat[ train_indices[i] ][ train_indices[j] ]
            for i in range(len(test_indices)):
                for j in range(len(train_indices)):
                    k_test[i][j] = k_mat[ test_indices[i] ][ train_indices[j] ]

            # Train SVM regressor using precomputed kernel matrix
            model = svm.SVR("precomputed").fit(k_train, y_train)
            model.fit(k_train, y_train)

            # Evaluate model against the embeddedings of the test graphs
            y_pred = model.predict(k_test)
             
            # Print progress
            print("Done with split {}/{}".format(split_idx+1, n_folds))
            print()

            # Aggregate results for this fold
            true_nd_vals += list(y_test)
            pred_nd_vals += list(y_pred)
        
        # Aggregate results for this vertex labeling
        vertex_labeling_to_results[ requested_vertex_label ] = { "true" : true_nd_vals, "pred" : pred_nd_vals }

    return vertex_labeling_to_results


def evaluate_wlst_kernel( graphs, graph_labels, wl_iter_range, label_requests, n_folds=10, seed=None ):
    """
    """

    # Print progress
    print("Evaluating Weisfeiler-Lehman Subtree-Pattern Kernel")
    print()
    
    # Just a few sanity checks
    assert( len(graphs) == len(graph_labels) )
    
    # Mapping from vertex labeling to results
    vertex_labeling_to_results = {}

    # Sweep over vertex label options
    for lr in label_requests:
        
        # Unpack
        requested_vertex_label = lr["vertex"]

        # Print progress
        print("Vertex Label: {}".format(requested_vertex_label))
        print()

        # Convert the base graphs into representations with
        # the requested vertex and edge labels, if any.
        relabeled_graphs = [ relabel_for_wlst_kernel(g, label=requested_vertex_label) for g in graphs ]
        
        # Store results for this vertex labeling
        n_iters_to_results = {}

        # Sweep over WL-iteration range
        for n_wl_iters in wl_iter_range:

            # Print progress
            print("# WL-Iterations: {}".format(n_wl_iters))
            print()
        
            # Compute kernel matrix
            k_mat = gk.CalculateWLKernel( relabeled_graphs, n_wl_iters )

            # Define lists to track non-determinism fraction prediction results 
            # over multiple folds
            true_nd_vals = []
            pred_nd_vals = []
            
            # Define training and testing sets
            graph_indices = list(range(len(graph_labels)))
            kf = KFold(n_splits=n_folds, random_state=seed, shuffle=True)
            for split_idx, (train_indices, test_indices) in enumerate(kf.split(graph_indices)):
                
                # Print progress
                print("Running split {}/{}".format(split_idx+1, n_folds))

                # Get training and testing graphs
                g_train = [ relabeled_graphs[i] for i in train_indices ]
                g_test = [ relabeled_graphs[i] for i in test_indices ]

                # Get the non-determinism fraction values for the training and 
                # testing graphs
                y_train = [ graph_labels[i] for i in train_indices ]
                y_test = [ graph_labels[i] for i in test_indices ]

                # Retrieve embeddings of training and test graphs
                k_train = np.zeros((len(train_indices), len(train_indices)))
                k_test  = np.zeros((len(test_indices), len(train_indices)))
                for i in range(len(train_indices)):
                    for j in range(len(train_indices)):
                        k_train[i][j] = k_mat[ train_indices[i] ][ train_indices[j] ]
                for i in range(len(test_indices)):
                    for j in range(len(train_indices)):
                        k_test[i][j] = k_mat[ test_indices[i] ][ train_indices[j] ]
                
                # Train SVM regressor using precomputed kernel matrix
                model = svm.SVR("precomputed").fit(k_train, y_train)
                model.fit(k_train, y_train)

                # Evaluate model against the embeddedings of the test graphs
                y_pred = model.predict(k_test)
                 
                # Print progress
                print("Done with split {}/{}".format(split_idx+1, n_folds))
                print()

                # Aggregate results for this fold
                true_nd_vals += list(y_test)
                pred_nd_vals += list(y_pred)
            
            # Aggregate results for this # iterations
            n_iters_to_results[n_wl_iters] = { "true" : true_nd_vals, "pred" : pred_nd_vals } 
        
        # Aggregate results for this vertex labeling
        vertex_labeling_to_results[ requested_vertex_label ] = n_iters_to_results

    return vertex_labeling_to_results


def main( traces_root_dir, output_path ):
    #base_kernel_defs = load_base_kernel_defs()
    #wl_kernel_defs = get_wl_kernel_defs(base_kernel_defs)
    #hc_kernel_defs = get_hc_kernel_defs(base_kernel_defs)
    #cf_kernel_defs = get_cf_kernel_defs(base_kernel_defs)
    #event_graph_attributes = load_event_graph_attributes()
    
    # Associate each graph with its label
    print("Getting graph labels...")
    slice_path_to_label = label_slices( traces_root_dir )
    graph_labels = [ slice_path_to_label[p] for p in sorted( slice_path_to_label.keys() ) ]
    
    # Ingest graphs 
    print("Ingesting graphs...")
    graphs = load_graphs( slice_path_to_label )

    graphs = [ compute_extra_labels(g) for g in graphs ]
  
    # Define graph kernels we will evaluate
    test_kernel_defs = [ 
                         #{"name" : "vertex_histogram"},
                         [{"name": "weisfeiler_lehman", "n_iter": 10}, {"name": "subtree_wl"}]
                       ]

    # Define graph labels we will evaluate
    wlst_label_requests = [ 
                            {"vertex" : "process_id", "edge" : None},
                            {"vertex" : "adjusted_logical_time", "edge" : None},
                            {"vertex" : "logical_time_increment", "edge" : None}
                          ]
    vh_label_requests = [ 
                          {"vertex" : "adjusted_logical_time", "edge" : None},
                          {"vertex" : "logical_time_increment", "edge" : None}
                        ]
    kernel_name_to_label_requests = { "weisfeiler_lehman_subtree_wl" : wlst_label_requests,
                                      "vertex_histogram"  : vh_label_requests
                                    }
    
    print("Starting evaluation...")
    print()

    kernel_to_results = {}
    for k_def in test_kernel_defs:
        # Get kernel name from kernel definition
        # This will be used later to identify the results
        kernel_name = get_name_from_kernel_def( k_def )

        # Look up the vertex/edge labeling requests for the current kernel
        label_requests = kernel_name_to_label_requests[ kernel_name ]

        # Train models
        # TODO: Figure out why GraKeL vertex histogram is throwing errors on
        # logical timestamp-labeled event graphs for message race pattern
        # For now, we substitute the graphkernels package implementation 
        if kernel_name == "vertex_histogram":
            results = evaluate_vertex_histogram_kernel( graphs, graph_labels, label_requests )
        elif kernel_name == "weisfeiler_lehman_subtree_wl":
            #wl_iter_range = [5, 10, 20, 40]
            wl_iter_range = [ 2, 4, 6, 8, 10 ]
            #wl_iter_range = [60, 80, 100]
            results = evaluate_wlst_kernel( graphs, graph_labels, wl_iter_range, label_requests )
        else:
            results = evaluate_kernel( graphs, graph_labels, k_def, label_requests )

        # Associate results with vertex/edge labeling 
        # We do this to assess the effect of different labeling schemes 
        # on model performance 
        #labeling_to_results = { get_name_from_label_request(lr):res for lr,res in zip(label_requests, results) }
        
        # Aggregate results
        kernel_to_results[ kernel_name ] = results

    with open( output_path, "wb" ) as outfile:
        pkl.dump( kernel_to_results, outfile )





if __name__ == "__main__":
    desc = "Computes correlation between kernel distance and non-determinism fraction for naive reduce example"
    parser = argparse.ArgumentParser(description=desc)
    parser.add_argument("traces_root_dir",
                        help="The top-level directory containing as subdirectories all the traces of the runs for which this kernel distance time series will be computed")  
    parser.add_argument("-o", "--output_path")
    #parser.add_argument("kernel_file", 
    #                    help="A JSON file describing the graph kernels that will be computed for each set of slice subgraphs")
    args = parser.parse_args()

    #main( args.traces_root_dir, args.kernel_file ) 
    main( args.traces_root_dir, args.output_path ) 

