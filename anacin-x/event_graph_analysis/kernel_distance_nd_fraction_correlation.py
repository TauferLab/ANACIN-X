#!/usr/bin/env python3 

import argparse
import pickle as pkl
import numpy as np
from scipy.stats.stats import pearsonr, spearmanr
import pprint

import sys
sys.path.append(".")
sys.path.append("..")

from kernel_distance_time_series_postprocessing import get_distances_seq, get_stats_seq

def main( kdts_path, drop_zeros ):
    # Read in kdts data
    with open( kdts_path, "rb" ) as infile:
        slice_idx_to_data = pkl.load( infile )
    # Reduce to flat lists of distances
    gk = ('wlst','logical_time', 5)
    slice_indices = sorted( slice_idx_to_data.keys() )
    nd_fraction_labels = [ 0, 0.2, 0.3, 0.4, 0.5, 0.6, 0.7, 0.8, 0.9, 1.0 ]
    flat_dists_seq = get_distances_seq( slice_idx_to_data, slice_indices, gk )
    
    if drop_zeros:
        for i in range(1,len(flat_dists_seq)):
            dists = flat_dists_seq[i]
            without_zeros = list( filter(lambda x: x != 0, dists) )
            flat_dists_seq[i] = without_zeros

    #for i in range(len(flat_dists_seq)):
    #    dists = flat_dists_seq[i]
    #    n_zeros = 0
    #    for d in dists:
    #        if d == 0.0:
    #            n_zeros += 1
    #    percent_zeros = n_zeros / len(dists)
    #    print("% ND: {} --> # zeros: {}, % zeros: {}".format(nd_fraction_labels[i],n_zeros, percent_zeros))


    # Associate each kernel distance with the non-determinism fraction of the 
    # runs its generating graphs represent
    nd_fraction_seq = []
    dist_seq = []
    for i in range( len( nd_fraction_labels ) ):
        for d in flat_dists_seq[i]:
            nd_fraction_seq.append( nd_fraction_labels[i] )
            dist_seq.append( d )

    pearson_r, pearson_p = pearsonr( nd_fraction_seq, dist_seq )
    spearman_r, spearman_p = spearmanr( nd_fraction_seq, dist_seq )
    print("Kernel distance vs. % ND --> Pearson-R = {}, p = {}".format(pearson_r, pearson_p))
    print("Kernel distance vs. % ND --> Spearman-R = {}, p = {}".format(spearman_r, spearman_p))

    all_stats_seq = get_stats_seq( flat_dists_seq )
    for stat in [ "mean", "median", "max", "variance" ]:
        stats_seq = [ s[stat] for s in all_stats_seq ]
        pearson_r, pearson_p = pearsonr( nd_fraction_labels, stats_seq )
        spearman_r, spearman_p = spearmanr( nd_fraction_labels, stats_seq )
        print("Kernel distance {} vs. % ND --> Pearson-R = {}, p = {}".format(stat, pearson_r, pearson_p))
        print("Kernel distance {} vs. % ND --> Spearman-R = {}, p = {}".format(stat, spearman_r, spearman_p))




if __name__ == "__main__":
    desc = "Computes correlation between kernel distance and non-determinism fraction for naive reduce example"
    parser = argparse.ArgumentParser(description=desc)
    parser.add_argument("kdts_path", 
                        help="Path to pickle file of kernel distance time series data")
    parser.add_argument("--drop_zeros", required=False, default=False, action="store_true",
                        help="Ignore identical runs when computing correlations")
    args = parser.parse_args()

    main( args.kdts_path, args.drop_zeros ) 

