import numpy as np
from scipy import stats

from graph_kernel_postprocessing import flatten_distance_matrix

def get_distances_seq( slice_idx_to_data, slice_indices, kernel ):
    distance_mat_seq = [ ]
    for idx in slice_indices:
        distance_mat_seq.append( slice_idx_to_data[ idx ][ "kernel_distance" ][ kernel ] )
    distances_seq = [ flatten_distance_matrix(dm) for dm in distance_mat_seq ]
    return distances_seq 


def describe_distances( distances ):
    descriptive_stats = { "min" : min( distances ),
                          "max" : max( distances ),
                          "median" : np.median( distances ),
                          "mean" : np.mean( distances ),
                          "variance" : np.var( distances ),
                          "skewness" : stats.skew( distances ),
                          "kurtosis" : stats.kurtosis( distances ) 
                        }
    return descriptive_stats

def get_stats_seq( distances_seq ):
    return [ describe_distances( d ) for d in distances_seq ]
