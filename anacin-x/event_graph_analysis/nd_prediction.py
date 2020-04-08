#!/usr/bin/env python3

import argparse
import pprint
import glob
import json
import os
import numpy as np

from sklearn.model_selection import train_test_split
from sklearn import svm
from sklearn.metrics import accuracy_score

from utilities import read_graph
from graph_kernel_preprocessing import get_relabeled_graphs, convert_to_grakel_graph

#import graphkernels
#import graphkernels.kernels as gk

from grakel import GraphKernel

import sys
sys.path.append(".")
sys.path.append("..")

def get_label( slice_path, nd_fraction_labels ):
    name, ext = os.path.splitext( os.path.basename( slice_path ) ) 
    label_idx = int( name[6:] )
    return nd_fraction_labels[ label_idx ]

def label_slices( traces_root_dir ):
    #nd_fraction_labels = [ 0, 0.2, 0.3, 0.4, 0.5, 0.6, 0.7, 0.8, 0.9, 1.0 ]
    nd_fraction_labels = [ 0, 10, 20, 30, 40, 50, 60, 70, 80, 90, 100 ]
    slice_dirs = glob.glob( traces_root_dir + "/run*/slices/" )
    slice_path_to_label = {}
    for sd in slice_dirs:
        slices = sorted( glob.glob( sd + "/*.graphml" ) )
        for s in slices:
            nd_fraction = get_label( s, nd_fraction_labels )
            slice_path_to_label[ s ] = nd_fraction
            #if nd_fraction < 50:
            #    slice_path_to_label[ s ] = 0
            #else:
            #    slice_path_to_label[ s ] = 1
    return slice_path_to_label

"""
Load GraKeL base graph kernel definitions/parameters from config file
"""
def load_base_kernels(base_kernels_path="grakel_base_kernels.json"):
    with open(base_kernels_path, "r") as infile:
        base_kernels = json.load(infile)
    return base_kernels


"""
Construct Weisfeiler-Lehman versions of all base kernels
"""
def define_wl_kernels(base_kernels, wl_iters=10):
    wl_kernels = {}
    for name,base_kernel in base_kernels.items():
        key = name + "_wl" 
        # Override base kernel's vertex label requirements
        constraints = base_kernel["constraints"]
        constraints["vertex_label"] = "needs"
        base_params = base_kernel["params"]
        wl_kernels[key] = {"constraints" : constraints, "params" : [{"name" : "weisfeiler_lehman", "n_iter" : wl_iters}, base_params]}
    return wl_kernels

"""
Construct Hadamard Code versions of all base kernels
"""
def define_hc_kernels(base_kernels):
    hadamard_code_kernels = {}
    for name,base_kernel in base_kernels.items():
        key = name + "_hc" 
        # Override base kernel's vertex label requirements
        constraints = base_kernel["constraints"]
        constraints["vertex_label"] = "needs"
        base_params = base_kernel["params"]
        hadamard_code_kernels[key] = {"constraints" : constraints, "params" : [{"name" : "hadamard_code"}, base_params]}
    return hadamard_code_kernels
                   

"""
Construct Core Framework versions of all base kernels
"""
def define_cf_kernels(base_kernels):
    core_framework_kernels = {}
    for name,base_kernel in base_kernels.items():
        key = name + "_cf" 
        constraints = base_kernel["constraints"]
        base_params = base_kernel["params"]
        core_framework_kernels[key] = {"constraints" : constraints, "params" : [{"name" : "core_framework"}, base_params]}
    return core_framework_kernels



def main( traces_root_dir, kernel_file ):
    base_kernels = load_base_kernels()
    wl_kernels = define_wl_kernels(base_kernels)
    hc_kernels = define_hc_kernels(base_kernels)
    cf_kernels = define_cf_kernels(base_kernels)

    # Read in kernel params 
    with open( kernel_file, "r" ) as infile:
        kernels = json.load( infile )["kernels"]

    # Associate each graph with its label
    slice_path_to_label = label_slices( traces_root_dir )
    labels = [ slice_path_to_label[p] for p in sorted( slice_path_to_label.keys() ) ]
    
    # Ingest graphs 
    graphs = [ read_graph(p) for p in sorted( slice_path_to_label.keys() ) ]
   
    # Relabel by selecting at most one vertex label and one edge label
    relabeled_graphs = get_relabeled_graphs( graphs, kernels )[ ('wlst','logical_time') ]

    # Convert to Grakel-compatible representation
    grakel_graphs = [ convert_to_grakel_graph(g) for g in relabeled_graphs ]
    
    # Perform cross validation for selected graph kernel
    scores = []
    for i in range(100):
        # Split into training vs. testing
        all_indices = list(range(len(labels)))
        train_indices, test_indices = train_test_split( all_indices, test_size=0.1, random_state=i )

        # Compute graph kernel
        g_train = [ grakel_graphs[i] for i in train_indices ]
        g_test = [ grakel_graphs[i] for i in test_indices ]
        kernel = [{"name": "weisfeiler_lehman", "n_iter": 10}, 
                  {"name": "subtree_wl"}]
        gk = GraphKernel(kernel=kernel, normalize=True)
        k_train = gk.fit_transform( g_train )
        k_test  = gk.transform( g_test )
        
        #print( k_train.shape )
        #print( k_test.shape )
        #exit()
        
        # Train classifier
        y_train = [ labels[i] for i in train_indices ]
        y_test = [ labels[i] for i in test_indices ]
        #clf = svm.SVC()
        #clf.fit(k_train, y_train)
        #y_pred = clf.predict(k_test)
        reg = svm.SVR()
        reg.fit(k_train, y_train)
        y_pred = reg.predict(k_test)
        
        rmse = 0
        for true,pred in zip(y_test,y_pred):
            rmse += (true - pred) ** 2
            print("True: {}, Predicted: {}".format(true,pred))
        rmse = np.sqrt(rmse / len(y_test))
        print("RMSE: {}".format(rmse))
        exit()

        accuracy = accuracy_score(y_test, y_pred)
        print("Round {}/100: accuracy = {}".format(i+1, accuracy))
        scores.append( accuracy )

    pprint.pprint( scores )
    print( np.mean( scores ) )


if __name__ == "__main__":
    desc = "Computes correlation between kernel distance and non-determinism fraction for naive reduce example"
    parser = argparse.ArgumentParser(description=desc)
    parser.add_argument("traces_root_dir",
                        help="The top-level directory containing as subdirectories all the traces of the runs for which this kernel distance time series will be computed")  
    parser.add_argument("kernel_file", 
                        help="A JSON file describing the graph kernels that will be computed for each set of slice subgraphs")
    args = parser.parse_args()

    main( args.traces_root_dir, args.kernel_file ) 

