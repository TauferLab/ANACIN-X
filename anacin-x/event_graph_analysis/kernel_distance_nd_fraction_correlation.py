#!/usr/bin/env python3 

import argparse
import pickle as pkl
import numpy as np
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
    dist_seq = get_distances_seq( slice_idx_to_data, slice_indices, gk )
    dist_stats_seq = get_stats_seq( dist_seq )

    nd_fractions = [ 0, 0.2, 0.3, 0.4, 0.5, 0.6, 0.7, 0.8, 0.9, 1.0 ]
    for stat in [ "min", "median", "mean", "max" ]:
        kd_seq = [ x[stat] for x in dist_stats_seq ]
        pearson_r = np.corrcoef( nd_fractions, kd_seq )[0][1]
        print("Kernel Distance {} correlates with ND Fraction w/ Pearson-R = {}".format(stat,pearson_r))

if __name__ == "__main__":
    desc = "Computes correlation between kernel distance and non-determinism fraction for naive reduce example"
    parser = argparse.ArgumentParser(description=desc)
    parser.add_argument("kdts_path", 
                        help="Path to pickle file of kernel distance time series data")
    args = parser.parse_args()

    main( args.kdts_path ) 

