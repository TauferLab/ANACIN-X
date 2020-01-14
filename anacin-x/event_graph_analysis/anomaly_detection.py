#!/usr/bin/env python3

import argparse
import pickle
import json
import os
import numpy as np
from scipy.stats import chisquare

import pprint

### Change-point analysis libraries
import ruptures as rpt


from utilities import timer

"""
Returns a list of pairwise kernel distances from a kernel distance matrix
"""
def get_flat_distances( distance_mat ):
    distances = []
    for i in range(len(distance_mat)):
        for j in range(len(distance_mat)):
            if i > j:
                distances.append( distance_mat[i][j] )
    return distances

"""
Groups distances into buckets where each bucket is an interval of [ low, high ]
and a distance d is grouped into a bucket if low <= d < high
"""
def bucket_distances( distances, buckets ):
    bucket_to_count = {}
    for d in distances:
        for i in range(1,len(buckets)):
            lower_bound = buckets[i-1]
            upper_bound = buckets[i]
            # Found bucket this distance falls into 
            if lower_bound <= b < upper_bound:
                bucket = ( lower_bound, upper_bound )
                if bucket not in bucket_to_count:
                    bucket_to_count[ bucket ] = 1
                else:
                    bucket_to_count[ bucket ] += 1
    return bucket_to_count

@timer
def detect_anomalies( kernel_distance_seq, policy ):
    # Unpack policy
    policy_name = policy["name"]
    policy_params = policy["params"]

    # Do a truly naive anomaly detection policy where we just define the slice 
    # containing the max kernel distance as anomalous and all others as not
    # anomalous. This is not really "anomaly detection" in any meaningful sense
    # But it suffices for testing the basic workflow
    if policy_name == "naive_max":
        max_dist_slice_idx = 0
        max_dist = 0
        for slice_idx,distance_mat in enumerate( kernel_distance_seq ):
            distances = get_flat_distances( distance_mat )
            slice_max = max( distances)
            if max_distance_in_slice > max_dist:
                max_dist = slice_max
                max_dist_slice_idx = slice_idx
        return [ max_dist_slice_idx ]

    # Detect anomalies based on whether the median kernel distance increases
    # from slice to slice or not
    elif policy_name == "increasing_median":
        flagged_slice_indices = []
        prev_median_distance = 0
        curr_median_distance = 0
        for slice_idx,distance_mat in enumerate( kernel_distance_seq ):
            distances = get_flat_distances( distance_mat )
            curr_median_distance = np.median( distances )
            if curr_median_distance > prev_median_distance:
                flagged_slice_indices.append( slice_idx )
            prev_median_distance = curr_median_distance
        return flagged_slice_indices

    # Flag slices if the median kernel distance exceeds a user-supplied 
    # threshold
    elif policy_name == "median_exceeds_threshold":
        threshold = policy_params[ "threshold" ]
        flagged_slice_indices = []
        for slice_idx,distance_mat in enumerate( kernel_distance_seq ):
            distances = get_flat_distances( distance_mat )
            median_distance = np.median( distances )
            if median_distance > threshold:
                flagged_slice_indices.append( slice_idx )
        return flagged_slice_indices
        
    # Randomly choose slices. This isn't really an anomaly detection policy, but
    # we use it to check whether the distribution of callstacks from a random
    # sample of slices looks different than the distribution of callstacks from
    # the flagged slices
    elif policy_name == "random":
        n_samples = policy_params["n_samples"]
        n_slices = len(kernel_distance_seq)
        n_generated = 0
        flagged_slice_indices = set()
        while n_generated < n_samples:
            # generate uniform random number between 0 and n_slices-1
            rand_slice_idx = np.random.randint( 0, n_slices, size=1 )[0]
            if rand_slice_idx not in flagged_slice_indices:
                flagged_slice_indices.add( rand_slice_idx )
                n_generated += 1
        return list( flagged_slice_indices )

    elif policy_name == "all":
        n_slices = len(kernel_distance_seq)
        return list( range( n_slices ) )
    
    elif policy_name == "ruptures_window_based":
        # Unpack policy
        model = policy_params[ "model" ]
        width = policy_params[ "width" ]
        n_change_points = policy_params[ "n_change_points" ]
        penalty = policy_params[ "penalty" ]
        epsilon = policy_params[ "epsilon" ]

        # Get list of distance distributions
        distance_distribution_seq = []
        for slice_idx,distance_mat in enumerate( kernel_distance_seq ):
            distances = get_flat_distances( distance_mat )
            distance_distribution_seq.append( distances )

        # Get some properties about the distances needed by Ruptures
        n_distributions = len( distance_distribution_seq )
        dim = len( distances )
        all_distances = []
        for d in distance_distribution_seq:
            all_distances += d
        sigma = np.std( all_distances )

        # Make into ndarray for ruptures
        signal = np.array( [ np.array(d) for d in distance_distribution_seq ] )

        # Set up model
        algo = rpt.Window( width=width, model=model ).fit( signal )

        # Find change-points
        if n_change_points == "unknown":
            if penalty == True and epsilon == False:
                penalty_value = np.log( n_distributions ) * dim * sigma**2 
                change_points = algo.predict( pen=penalty_value )
            elif penalty == False and epsilon == True:
                threshold = 3 * n_distributions * sigma**2
                change_points = algo.predict( epsilon=threshold )
            else:
                raise ValueError("Invalid policy for window-based change-point detection: {}".format(policy_params))
        else:
            change_points = algo.predict( n_bkps=n_change_points )
        
        flagged_slice_indices = [ cp-1 for cp in change_points ]
        return flagged_slice_indices
            

    

    ## Detect anomalies based on distance between distributions using the 
    ## chi-squared test statistic
    #elif policy_name == "chi_squared":
    #    n_buckets = policy["params"]["n_buckets"]
    #    flagged_slice_indices = []
    #    for slice_idx in enumerate( 1, kernel_distance_seq ):
    #        # Get the distances for current slice and its predecessor
    #        prev_slice_distances = get_flat_distances( kernel_distance_seq[ slice_idx-1 ] )
    #        curr_slice_distances = get_flat_distances( kernel_distance_seq[ slice_idx ] )
    #        # Get extrema for the distances in these pairs of distance observations
    #        min_dist = min( prev_slice_distances + curr_slice_distances )
    #        max_dist = max( prev_slice_distances + curr_slice_distances )
    #        # Define buckets based on extrema and desired number of buckets
    #        buckets = np.linspace( min_dist, max_dist, n_buckets+1, endpoint=True )
    #        # Bucket distance values
    #        prev_slice_bucketed_distances = bucket_distances( prev_slice_distances, buckets )
    #        curr_slice_bucketed_distances = bucket_distances( curr_slice_distances, buckets )
    #        # Compute test statistic for this pair of slices
    #        observed_frequencies = [ v for k,v in sorted(prev_slice_bucketed_distances.items()) ]
    #        expected_frequencies = [ v for k,v in sorted(curr_slice_bucketed_distances.items()) ]
    #        #test_statistic = 0
    #        #for bucket in sorted( prev_slice_bucketed_distances.keys() ):
    #        #    prev_slice_count = prev_slice_bucketed_distances[ bucket ] 
    #        #    curr_slice_count = curr_slice_bucketed_distances[ bucket ] 
    #        #    contribution = ( ( prev_slice_count - curr_slice_count ) ** 2 ) / prev_slice_count
    #        #    test_statistic += contribution
    #        ## Check whether we reject the null hypothesis that the current 
    #        ## slice's distances are drawn from the same distribution as the 
    #        ## previous slice's
    #        #n_degrees_of_freedom = n_buckets - 1

            

     
    else:
        raise NotImplementedError("Anomaly detection policy: {} is not implemented".format(policy_name))
    

@timer
def main( kernel_distance_data_path, policy_file_path, output_path ):
    # Read in kernel distance time series data
    with open( kernel_distance_data_path, "rb" ) as infile:
        slice_idx_to_data = pickle.load( infile )

    # Read in anomaly detection policies
    with open( policy_file_path, "r" ) as infile:
        anomaly_detection_policies = json.load( infile )

    # Choose a kernel
    chosen_kernel = ( "wlst", "logical_time", 5 )
    #chosen_kernel = ( "wlst", 5, "logical_time")

    # Filter down to a kernel distance time series w/r/t that kernel
    kernel_distances_seq = []
    for idx,kvp in enumerate( sorted(slice_idx_to_data.items()) ):
        slice_idx,data = kvp
        kernel_distances_seq.append( data["kernel_distance"][chosen_kernel] )

    # Do a pass over the kernel distance time series for each policy
    # For right now, we do an independent pass over the kernel distance data
    # for each anomaly detection policy 
    policy_to_flagged_slice_indices = {}
    for policy in anomaly_detection_policies["policies"]:
        flagged_indices = detect_anomalies( kernel_distances_seq, policy )
        policy_key = policy["name"]
        policy_to_flagged_slice_indices[ policy_key ] = flagged_indices

    #pprint.pprint( policy_to_flagged_slice_indices )
    #exit()

    # Determine output path
    kdts_path = os.path.dirname( kernel_distance_data_path )
    if output_path is None:
        output_path = kdts_path + "/flagged_indices.pkl"
    else:
        name,ext = os.path.splitext( output_path )
        if ext != ".pkl":
            output_path = kdts_path + "/" + name + ".pkl"
        else:
            output_path = kdts_path + "/" + output_path 
    
    # Write output
    with open( output_path, "wb" ) as outfile:
        pickle.dump( policy_to_flagged_slice_indices, outfile, pickle.HIGHEST_PROTOCOL )

if __name__ == "__main__":
    desc = "Performs anomaly detection on a time series of kernel distance data"
    parser = argparse.ArgumentParser(description=desc)
    parser.add_argument("kernel_distance_data", 
                        help="Path to pickle file of kernel distance time series data")
    parser.add_argument("anomaly_detection_policies", 
                        help="JSON file containing description of anomaly detection algorithms to run")
    parser.add_argument("-o", "--output_path", default=None,
                        action="store", type=str, required=False,
                        help="Path to write anomaly detection results to. Optional.")
    args = parser.parse_args()

    main( args.kernel_distance_data, 
          args.anomaly_detection_policies, 
          args.output_path )
