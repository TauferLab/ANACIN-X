
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

import sys
sys.path.append(".")
sys.path.append("..")
from event_graph_analysis.utilities import timer


@timer
def compute_kernel_matrix_grakel(event_graphs, kernel_params):
    kernel = GraphKernel(kernel_params)
    kernel_mat = kernel.fit_transform(event_graphs)
    return kernel_mat


def compute_unlabeled_shortest_path_kernel( labeling_to_graphs, k_params ):
    # Get unlabeled graphs
    graphs = labeling_to_graphs["unlabeled"]
    return compute_kernel_matrix_grakel( graphs, k_params )

def compute_labeled_shortest_path_kernel( labeling_to_graphs, k_params ):
    labeling_to_mat = {}
    for lab,graphs in labeling_to_graphs.items():
        if lab != "unlabeled":
            vertex_label = lab[0]
            labeling_to_mat[vertex_label] = compute_kernel_matrix_grakel( graphs, k_params )
    return labeling_to_mat
    
def compute_unlabeled_random_walk_kernel( labeling_to_graphs, k_params ):
    # Get unlabeled graphs
    graphs = labeling_to_graphs["unlabeled"]
    return compute_kernel_matrix_grakel( graphs, k_params )

def compute_labeled_random_walk_kernel( labeling_to_graphs, k_params ):
    labeling_to_mat = {}
    for lab,graphs in labeling_to_graphs.items():
        if lab != "unlabeled":
            vertex_label = lab[0]
            labeling_to_mat[vertex_label] = compute_kernel_matrix_grakel( graphs, k_params )
    return labeling_to_mat


def compute_neighborhood_hash_kernel( labeling_to_graphs, k_params ):
    labeling_to_mat = {}
    for lab,graphs in labeling_to_graphs.items():
        if lab != "unlabeled":
            vertex_label = lab[0]
            labeling_to_mat[vertex_label] = compute_kernel_matrix_grakel( graphs, k_params )
    return labeling_to_mat


def compute_odd_sth_kernel( labeling_to_graphs, k_params ):
    labeling_to_mat = {}
    for lab,graphs in labeling_to_graphs.items():
        if lab != "unlabeled":
            vertex_label = lab[0]
            labeling_to_mat[vertex_label] = compute_kernel_matrix_grakel( graphs, k_params )
    return labeling_to_mat


def compute_vertex_histogram_kernel( labeling_to_graphs, k_params ):
    labeling_to_results = {}
    for lab,graphs in labeling_to_graphs.items():
        if lab != "unlabeled":
            vertex_label = lab[0]
            labeling_to_results[vertex_label] = compute_kernel_matrix_grakel(graphs,k_params)
    return labeling_to_results


def compute_graphlet_sampling_kernel( labeling_to_graphs, sample_dims, sample_counts ):
    # Get unlabeled graphs
    graphs = labeling_to_graphs["unlabeled"]

    # Configure graphlet sampling parameters
    default_sample_counts = [10, 100]
    default_sample_dims = [3, 5]
    if sample_dims is None:
        sample_dims = default_sample_dims
    if sample_counts is None:
        sample_counts = default_sample_counts

    sample_dim_to_results = {}
    for dim in sample_dims:
        sample_count_to_mat = {}
        for count in sample_counts:
            if count == "all":
                # TODO: This breaks grakel impl.
                kernel = grakel.GraphletSampling(k=dim)
            else:
                kernel = grakel.GraphletSampling(k=dim, sampling={"n_samples":count})
            sample_count_to_mat[count] = kernel.fit_transform(graphs)
        sample_dim_to_results[dim] = sample_count_to_mat
    return sample_dim_to_results



def compute_wlst_kernel(labeling_to_graphs, wl_iters):
    default_wl_iters = [2, 4, 8]
    labeling_to_results = {}
    for lab,graphs in labeling_to_graphs.items():
        if lab != "unlabeled":
            vertex_label = lab[0]
            if wl_iters is None:
                wl_iters = default_wl_iters
            n_iters_to_matrix = {}
            for n_iter in wl_iters:
                k_params = [{"name" : "weisfeiler_lehman", "n_iter" : n_iter}, 
                            {"name" : "subtree_wl"}]
                n_iters_to_matrix[n_iter] = compute_kernel_matrix_grakel(graphs, k_params)
            labeling_to_results[vertex_label] = n_iters_to_matrix
    return labeling_to_results
                
            

