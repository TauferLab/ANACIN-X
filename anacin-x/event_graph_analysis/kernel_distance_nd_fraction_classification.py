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
    nd_fraction_labels = [ 0, 20, 30, 40, 50, 60, 70, 80, 90, 100 ]
    slice_dirs = glob.glob( traces_root_dir + "/run*/slices/" )
    slice_path_to_label = {}
    for sd in slice_dirs:
        slices = sorted( glob.glob( sd + "/*.graphml" ) )
        for s in slices:
            slice_path_to_label[ s ] = get_label( s, nd_fraction_labels )
    return slice_path_to_label

def main( traces_root_dir, kernel_file ):
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
        kernel = [{"name": "weisfeiler_lehman", "n_iter": 5}, 
                  {"name": "subtree_wl"}]
        gk = GraphKernel(kernel=kernel, normalize=True)
        k_train = gk.fit_transform( g_train )
        k_test  = gk.transform( g_test )

        #print( k_train.shape )
        #print( k_test.shape )
        
        # Train classifier
        y_train = [ labels[i] for i in train_indices ]
        y_test = [ labels[i] for i in test_indices ]
        clf = svm.SVC()
        clf.fit(k_train, y_train)
        y_pred = clf.predict(k_test)
        #print(str(round(accuracy_score(y_test, y_pred)*100, 2)), "%")
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

