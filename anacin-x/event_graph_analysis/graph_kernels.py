#!/usr/bin/env python3

#SBATCH -o graph_kernel_svr-%j.out
#SBATCH -e graph_kernel_svr-%j.err
#SBATCH -t 12:00:00

import argparse
import pprint

import re
import os
import glob
import json
import numpy as np
import pickle as pkl

# Import igraph bindings
import igraph

# Import Borgwardt Lab graph kernel implementations
import graphkernels
import graphkernels.kernels as gk

# Suppress sklearn deprecation warning from grakel
import warnings
warnings.simplefilter(action='ignore', category=FutureWarning)

# Import generic GraKeL graph kernel interface
import grakel
from grakel import GraphKernel

# Import event graph utilities
import sys
sys.path.append(".")
sys.path.append("..")
from event_graph_analysis.utilities import read_graph, read_run_params, timer
from event_graph_analysis.graph_kernel_preprocessing import relabel_for_wlst_kernel, convert_to_grakel_graph, add_logical_tick_labels
from event_graph_analysis.graph_kernel_utils import preprocess
from event_graph_analysis.graph_kernel_wrappers import (compute_wlst_kernel,
                                                        compute_vertex_histogram_kernel,
                                                        compute_graphlet_sampling_kernel,
                                                        compute_unlabeled_shortest_path_kernel,
                                                        compute_unlabeled_random_walk_kernel,
                                                        compute_labeled_shortest_path_kernel,
                                                        compute_labeled_random_walk_kernel,
                                                        compute_neighborhood_hash_kernel,
                                                        compute_odd_sth_kernel
                                                       )

# Imports for training SVRs
from sklearn.model_selection import train_test_split, KFold, GridSearchCV
from sklearn import svm
from sklearn.metrics import accuracy_score, mean_squared_error

#@timer
#def preprocess_graphs_gk(event_graphs):
#    graphs = [ data["event_graph"] for rd,data in sorted(event_graphs.items()) ]
#    relabeled_graphs = [ relabel_for_wlst_kernel(g, label="logical_time") for g in graphs ]
#    return relabeled_graphs
#
#@timer
#def compute_kernel_matrix_gk(event_graphs, kernel=None):
#    kernel_mat = gk.CalculateWLKernel( event_graphs, 5 )
#    return kernel_mat

@timer
def preprocess_graphs_grakel(event_graphs, label_req):
    graphs = [ data["event_graph"] for rd,data in sorted(event_graphs.items()) ]
    relabeled_graphs = [ convert_to_grakel_graph(g, label_req) for g in graphs ]
    return relabeled_graphs


@timer
def compute_kernel_matrix_grakel(event_graphs, kernel_params):
    kernel = GraphKernel(kernel_params)
    kernel_mat = kernel.fit_transform(event_graphs)
    return kernel_mat

@timer
def compute_graphlet_sampling_kernel_matrix_grakel(event_graphs, n_samples, sample_dim):
    if n_samples == "all":
        kernel = grakel.GraphletSampling(k=sample_dim)
        kernel_mat = kernel.fit_transform(event_graphs)
    else:
        kernel = grakel.GraphletSampling(k=sample_dim, sampling={"n_samples":n_samples})
        kernel_mat = kernel.fit_transform(event_graphs)
    return kernel_mat

def get_ground_truth_labels(event_graphs):
    true_ndp = [ data["run_params"]["nd_percentage_msg"] for rd,data in sorted(event_graphs.items()) ]
    return true_ndp


def get_k_train(k_mat, train_indices):
    n = len(train_indices)
    k_train = np.zeros((n,n))
    for i in range(n):
        for j in range(n):
            k_train[i][j] = k_mat[train_indices[i]][train_indices[j]]
    return k_train


def get_k_test(k_mat, train_indices, test_indices):
    n = len(train_indices)
    m = len(test_indices)
    k_test = np.zeros((m,n))
    for i in range(m):
        for j in range(n):
            k_test[i][j] = k_mat[test_indices[i]][train_indices[j]]
    return k_test


def select_runs(run_dirs, max_run_idx):
    selected_runs = []
    for rd in run_dirs:
        run_idx = int(re.sub("[^0-9]", "", os.path.basename(rd)))
        if run_idx <= max_run_idx:
            selected_runs.append(rd)
    return selected_runs

@timer
def load_event_graphs(base_dir, depth=0, max_run_idx=None, eg_ext="graphml"):
    glob_path = base_dir
    for _ in range(depth):
        glob_path += "/*/"
    glob_path += "/run_*"
    # Don't actually need to sort here, but helps debugging output
    run_dirs = sorted(glob.glob(glob_path)) 
    if max_run_idx is not None:
        run_dirs = select_runs(run_dirs, max_run_idx)
    # Get the event graphs and their run parameter data
    event_graphs = { rd:{"event_graph":read_graph(rd+"/event_graph."+eg_ext),
                         "run_params":read_run_params(rd+"/run_params.json")}
                     for rd in run_dirs
                   }
    return event_graphs


def load_base_kernel_defs(base_kernels_path):
    """
    Load GraKeL base graph kernel definitions/parameters from config file
    """
    with open(base_kernels_path, "r") as infile:
        base_kernels = json.load(infile)
    return base_kernels







def main2(base_dir, run_dir_depth, cached_kernel_matrices, max_run_idx):
    
    # Locations of base kernel definition JSON files
    base_kernels_path="config/graph_kernels/grakel_base_kernels.json"
    graph_attributes_path="config/graph_kernels/event_graph_attributes.json"

    # Load base kernel definitions
    base_kernel_defs = load_base_kernel_defs(base_kernels_path)
    
    # Define possible graph labeling requests
    label_requests = [ {"vertex" : "process_id", "edge" : None},
                       {"vertex" : "logical_time", "edge" : None},
                       {"vertex" : "logical_tick", "edge" : None} ]

    # Load event graphs
    event_graphs = get_event_graphs(base_dir, depth=run_dir_depth, max_run_idx=max_run_idx)

    # Load event graph "class" labels
    true_ndp = get_ground_truth_labels(event_graphs)

    graphlet_sampling_params = { "n_samples" : [ 4, 8, 16 ],
                                 "sample_dim" : [ 3, 5, 7 ] 
                               }

    # Define a set of kernels to test
    #test_kernels = [ "random_walk" ]
    #test_kernels = [ "shortest_path" ]
    #test_kernels = [ "random_walk" , "shortest_path" ]
    test_kernels = []
    
    #test_kernels = [ "vertex_histogram" ]
    #test_kernels = [
    #                "graphlet_sampling"
    #               ]

    # Load in existing kernel matrices to make sure we do not duplicate
    if cached_kernel_matrices is not None and os.path.isfile(cached_kernel_matrices):
        print("Loading pre-computed kernel matrices")
        with open(cached_kernel_matrices, "rb") as infile:
            kdef_to_kmat = pkl.load(infile)
            print("Kernels already computed:")
            for k in kdef_to_kmat:
                print("\t{}".format(k))
    else:
        print("No precomputed kernels available")
        kdef_to_kmat = {}

    # Loop over base kernels and construct kernel matrices
    for k_name,k_def in base_kernel_defs.items():
        
        # Check if we're considering this kernel currently. If not, skip.
        if k_name in test_kernels:
            
            if k_name == "graphlet_sampling":
                n_samples_options = graphlet_sampling_params["n_samples"]
                sample_dim_options = graphlet_sampling_params["sample_dim"]
                for n_samples in n_samples_options:
                    for sample_dim in sample_dim_options:
                        key = (k_name, n_samples, sample_dim)
                        if key not in kdef_to_kmat:
                            print("Computing kernel matrix for: {}".format(key))
                            graphs = preprocess_graphs_grakel(event_graphs, None)
                            k_mat = compute_graphlet_sampling_kernel_matrix_grakel(graphs, n_samples, sample_dim)
                            kdef_to_kmat[key] = k_mat
                # Cmpute the exhaustive versions too
                for sample_dim in sample_dim_options:
                    key = (k_name, "all", sample_dim)
                    if key not in kdef_to_kmat:
                        print("Computing kernel matrix for: {}".format(key))
                        graphs = preprocess_graphs_grakel(event_graphs, None)
                        k_mat = compute_graphlet_sampling_kernel_matrix_grakel(graphs, n_samples, sample_dim)
                        kdef_to_kmat[key] = k_mat

            # Check if this kernel needs vertex relabeling
            if k_def["constraints"]["vertex_label"] == "needs":
                for req in label_requests:
                    key = (k_name, req["vertex"])
                    if key not in kdef_to_kmat:
                        print("Computing kernel matrix for: {}".format(key))
                        graphs = preprocess_graphs_grakel(event_graphs, req)
                        k_mat = compute_kernel_matrix_grakel(graphs, k_def["params"])
                        kdef_to_kmat[key] = k_mat
            else:
                if k_name not in ["graphlet_sampling"]:
                    key = tuple([k_name])
                    if key not in kdef_to_kmat:
                        print("Computing kernel matrix for: {}".format(key))
                        graphs = preprocess_graphs_grakel(event_graphs, None)
                        k_mat = compute_kernel_matrix_grakel(graphs, k_def["params"])
                        kdef_to_kmat[key] = k_mat
    
    # Loop over WL kernels and construct kernel matrices
    wl_iter_counts = [ 1, 100 ]
    for req in label_requests:
        for n_iter in wl_iter_counts:
            k_params = [{"name" : "weisfeiler_lehman", "n_iter" : n_iter}, {"name" : "subtree_wl"}]
            key = ("wlst", req["vertex"], n_iter)
            if key not in kdef_to_kmat:
                print("Computing kernel matrix for: {}".format(key))
                graphs = preprocess_graphs_grakel(event_graphs, req)
                k_mat = compute_kernel_matrix_grakel(graphs, k_params)
                kdef_to_kmat[key] = k_mat
    
    with open("kernel_matrices.pkl", "wb") as outfile:
        pkl.dump(kdef_to_kmat, outfile, protocol=0)

   
    results_path = "kdef_to_results.pkl"
    if os.path.exists(results_path):
        with open("kdef_to_results.pkl", "rb") as infile:
            kdef_to_results = pkl.load(infile)
    else:
        kdef_to_results = {}
    
    for k_def,k_mat in kdef_to_kmat.items():

        if k_def not in kdef_to_results:

            print("Training model using kernel: {}".format(k_def))
            print()

            # Flag to determine whether or not SVR hyperparamters have been 
            # determined already by grid search
            svr_hyperparams_set = False

            # SVR hyperparamters to search over
            svr_params = {'C':[1e0, 1e1, 1e2, 1e3], 'epsilon':[0.1,0.2,0.3,0.4,0.5]}
            optimal_params = {}

            # Random seed for k-fold CV
            seed = 0
            

            # K-fold cross-validation
            fold_to_results = {}
            kf = KFold(n_splits=10, random_state=seed, shuffle=True)
            for split_idx, (train_indices, test_indices) in enumerate(kf.split(range(len(event_graphs)))):

                # Get test-train split
                y_train = [ true_ndp[i] for i in train_indices ]
                y_test = [ true_ndp[i] for i in test_indices ]
                k_train = get_k_train(k_mat, train_indices )
                k_test = get_k_test(k_mat, train_indices, test_indices )

                #if not svr_hyperparams_set:
                #    svr = svm.SVR(kernel="precomputed")  
                #    model_family = GridSearchCV(svr, svr_params)
                #    model_family.fit(k_train, y_train)
                #    optimal_params = model_family.best_params_
                #    curr_svr = svm.SVR(kernel="precomputed", C=optimal_params["C"], epsilon=optimal_params["epsilon"])
                #    svr_hyperparams_set = True
                #else:
                #    curr_svr = svm.SVR(kernel="precomputed", C=optimal_params["C"], epsilon=optimal_params["epsilon"])
                
                # Initialize SVR model
                curr_svr = svm.SVR(kernel="precomputed")
                
                # Train SVR model
                curr_svr.fit(k_train, y_train)

                # Predict
                y_pred = curr_svr.predict(k_test)
                
                # Record model params and perf
                relative_errors = []
                for tv,pv in zip(y_test, y_pred):
                    rel_error = np.abs(tv - pv)/tv
                    relative_errors.append(rel_error)
                print("Split: {}".format(split_idx))
                print("Min Rel. Error: {}".format(min(relative_errors)))
                print("Median Rel. Error: {}".format(np.median(relative_errors)))
                print("Max Rel. Error: {}".format(max(relative_errors)))
                print()

                results = { "true" : y_test, "pred" : y_pred, "svr_params" : optimal_params }
                fold_to_results[ split_idx ] = results
            kdef_to_results[k_def] = fold_to_results
        
    with open(results_path, "wb") as results_outfile:
        pkl.dump(kdef_to_results, results_outfile, protocol=0)


def run_dir_to_key(rd):
    parts = rd.split("/")
    run_idx_part = parts[-1] 
    ndp_part = parts[-2]
    run_idx = int(re.sub(r"[^0-9]", "", run_idx_part))
    ndp = int(re.sub(r"[^0-9]", "", ndp_part))
    return (ndp, run_idx)

def main(base_dir, 
         run_dir_depth, 
         kernels, 
         labeling_path, 
         max_run_idx, 
         kernel_matrices_cache, 
         kernel_matrices_output, 
         wl_iters=None,
         graphlet_sampling_dims=None,
         graphlet_sampling_counts=None
        ):

    # Load requested graph labeling options
    with open(labeling_path, "r") as infile:
        labeling_requests = json.load(infile)

    # Locations of base kernel definition JSON files
    base_kernels_path="config/graph_kernels/grakel_base_kernels.json"
    graph_attributes_path="config/graph_kernels/event_graph_attributes.json"

    # Load base kernel definitions
    base_kernel_defs = load_base_kernel_defs(base_kernels_path)
    
    # Load event graphs
    run_dir_to_data = load_event_graphs(base_dir, depth=run_dir_depth, max_run_idx=max_run_idx)
    
    event_graphs = []
    run_params = []
    for rd,data in sorted(run_dir_to_data.items(), key=lambda x: run_dir_to_key(x[0])):
        event_graphs.append( data["event_graph"] )
        run_params.append( data["run_params"] )
    
    # Preprocess graphs as-needed based on requested kernels and labelings
    labeling_to_graphs = preprocess( event_graphs, base_kernel_defs, kernels, labeling_requests )
    
    # Storage for graph kernels computed in this run
    kernel_to_matrix = {}

    # Loop over base kernels and construct kernel matrices
    for k_id,k_def in base_kernel_defs.items():
        
        # Check if we're considering this kernel currently. If not, skip.
        if k_id in kernels:
            
            # Handle WLST case
            if k_id == "subtree_wl":
                kernel_to_matrix[k_id] = compute_wlst_kernel(labeling_to_graphs, wl_iters)

            # Handle Vertex Histogram case
            elif k_id == "vertex_histogram":
                kernel_to_matrix[k_id] = compute_vertex_histogram_kernel(labeling_to_graphs, k_def["params"])
            
            # Handle graphlet sampling case
            elif k_id == "graphlet_sampling":
                kernel_to_matrix[k_id] = compute_graphlet_sampling_kernel(labeling_to_graphs, 
                                                                          graphlet_sampling_dims, 
                                                                          graphlet_sampling_counts)

            # Handle unlabeled shortest path case
            elif k_id == "shortest_path":
                kernel_to_matrix[k_id] = compute_unlabeled_shortest_path_kernel(labeling_to_graphs, k_def["params"])

            # Handle unlabeled random walk case
            elif k_id == "random_walk":
                kernel_to_matrix[k_id] = compute_unlabeled_random_walk_kernel(labeling_to_graphs, k_def["params"])
            
            # Handle labeled shortest path case
            elif k_id == "shortest_path_labeled":
                kernel_to_matrix[k_id] = compute_labeled_shortest_path_kernel(labeling_to_graphs, k_def["params"])

            # Handle labeled random walk case
            elif k_id == "random_walk_labeled":
                kernel_to_matrix[k_id] = compute_labeled_random_walk_kernel(labeling_to_graphs, k_def["params"])

            # Handle neighborhood hash case
            elif k_id == "neighborhood_hash":
                kernel_to_matrix[k_id] = compute_neighborhood_hash_kernel(labeling_to_graphs, k_def["params"])
            
            # Handle odd-sth case
            elif k_id == "odd_sth":
                kernel_to_matrix[k_id] = compute_odd_sth_kernel(labeling_to_graphs, k_def["params"])



    pprint.pprint(kernel_to_matrix)




if __name__ == "__main__":
    desc = "Driver script for computing graph kernels on communication pattern event graphs"
    parser = argparse.ArgumentParser(description=desc)

    parser.add_argument("--base_dir", required=True, help="Directory with child directories containing all event graphs to compute kernel similarities for")
    parser.add_argument("--run_dir_depth", required=True, type=int, help="Number of levels down from base_dir to look for individual run directories")
    
    parser.add_argument("--kernels", required=True, nargs="+", help="List of graph kernels to evaluate")
    parser.add_argument("--labeling", required=False, default=None, help="Path to a JSON file describing all of the requested event graph labelings. If one of the requested graph kernels in [kernels] requires labeling labeling must be provided.")
    
    parser.add_argument("--max_run_idx", required=False, type=int, default=None, help="Number of runs from each run configuration to load event graphs from. If ommitted, all runs will be used.")
    
    parser.add_argument("--kernel_matrices_cache", required=False, default=None, help="Path to a pickle file containing previously computed kernel matrices") 
    parser.add_argument("--kernel_matrices_output", required=False, default=None, help="Path to write pickled mapping from kernels to kernel matrices") 
    
    # Optional arguments for configuring specific graph kernels
    parser.add_argument("--wl_iters", required=False, default=None, nargs="+", help="List of WL-iteration counts if using the subtree_wl kernel")
    parser.add_argument("--graphlet_sampling_dims", required=False, default=None, nargs="+", help="List of graphlet dimensions if using the graphlet_sampling kernel")
    parser.add_argument("--graphlet_sampling_counts", required=False, default=None, nargs="+", help="List of graphlet counts if using the graphlet_sampling kernel")


    args = parser.parse_args()
    
    
    main(args.base_dir, 
         args.run_dir_depth, 
         args.kernels,
         args.labeling,
         args.max_run_idx,
         args.kernel_matrices_cache, 
         args.kernel_matrices_output,
         wl_iters=args.wl_iters,
         graphlet_sampling_dims=args.graphlet_sampling_dims,
         graphlet_sampling_counts=args.graphlet_sampling_counts)
