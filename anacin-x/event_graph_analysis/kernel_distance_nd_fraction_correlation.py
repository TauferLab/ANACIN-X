#!/usr/bin/env python3 

import argparse
import pickle as pkl
import numpy as np
from scipy.stats.stats import pearsonr
import pprint

import sys
sys.path.append(".")
sys.path.append("..")

from kernel_distance_time_series_postprocessing import get_distances_seq, get_stats_seq

def main( kdts_path ):
    # Read in kdts data
    with open( kdts_path, "rb" ) as infile:
        slice_idx_to_data = pkl.load( infile )
    # Reduce to flat lists of distances
    gk = ('wlst','logical_time', 5)
    slice_indices = sorted( slice_idx_to_data.keys() )
    nd_fraction_labels = [ 0, 0.2, 0.3, 0.4, 0.5, 0.6, 0.7, 0.8, 0.9, 1.0 ]
    flat_dists_seq = get_distances_seq( slice_idx_to_data, slice_indices, gk )
    # Associate each kernel distance with the non-determinism fraction of the 
    # runs its generating graphs represent
    nd_fraction_seq = []
    dist_seq = []
    for i in range( len( nd_fraction_labels ) ):
        for d in flat_dists_seq[i]:
            nd_fraction_seq.append( nd_fraction_labels[i] )
            dist_seq.append( d )

    pearson_r, significance = pearsonr( nd_fraction_seq, dist_seq )
    print("Kernel Distance correlates with ND Fraction w/ Pearson-R = {}, significance = {}".format(pearson_r, significance))

if __name__ == "__main__":
    desc = "Computes correlation between kernel distance and non-determinism fraction for naive reduce example"
    parser = argparse.ArgumentParser(description=desc)
    parser.add_argument("kdts_path", 
                        help="Path to pickle file of kernel distance time series data")
    args = parser.parse_args()

    main( args.kdts_path ) 

