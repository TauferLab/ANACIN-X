#!/usr/bin/env python3

#SBATCH -n 1
#SBATCH -n 1
#SBATCH -t 01:00:00
#SBATCH -o make_mini_amr_kdts_plot-%j.out
#SBATCH -e make_mini_amr_kdts_plot-%j.err

import argparse
import pickle as pkl
import json
import os

import numpy as np

import matplotlib
matplotlib.use('TkAgg')
import matplotlib.pyplot as plt
from scipy.stats.stats import pearsonr, spearmanr

import pprint

import sys
sys.path.append("..")
sys.path.append(".")

from graph_kernel_postprocessing import flatten_distance_matrix


def kernel_json_to_key( kernel_json ):
    kernel_params = kernel_json["kernels"]
    assert( len(kernel_params) == 1 )
    kernel_params = kernel_params[0]
    kernel_name = kernel_params["name"]
    if kernel_name == "wlst":
        label = kernel_params["params"]["label"]
        n_iters = kernel_params["params"]["n_iters"]
        key = ( kernel_name, label, n_iters )
        return key
    else:
        raise NotImplementedError("Translation not implemented for kernel: {}".format(kernel_name))


def main( kdts_data_path, kernel_file_path, block_traffic_data_path=None, flagged_slices=None, kdts_ymax=None, mre_ymax=None, output="mini_amr_kdts.png"):

    # Read in kernel distance time series data
    with open( kdts_data_path, "rb" ) as infile:
        slice_idx_to_data = pkl.load( infile )

    # Read in kernel definition file
    with open( kernel_file_path, "r" ) as infile:
        kernel = json.load(infile)
   

    # Unpack kernel distance time series data
    slice_indices = sorted( slice_idx_to_data.keys() )
    kernel_key = kernel_json_to_key( kernel )
    kernel_matrices = [ slice_idx_to_data[i]["kernel_distance"][kernel_key] for i in slice_indices ]
    kernel_distances = [ flatten_distance_matrix(km) for km in kernel_matrices ]

    # Get x-axis positions for kernel distance distribution boxes
    kdts_box_positions = slice_indices
    
    # Get boxplot data 
    kdts_box_data = kernel_distances

    # Configure figure
    base_figure_size = (16, 9)
    figure_scale = 1.5
    figure_size = [ dim * figure_scale for dim in base_figure_size ]
    
    # Make figure and axis for kernel distance time series boxplot
    fig, kdts_ax = plt.subplots( figsize = figure_size )

    # Configure boxplot appearance
    box_width = 0.5
    box_props = { "alpha" : 0.5 }
    flier_props = { "marker" : "+", "markersize" : 4 }
        
    if flagged_slices is not None:
        with open( flagged_slices, "rb" ) as infile:
            #flagged_indices = pkl.load( infile )["increasing_median"]  # TODO undo hardcode
            flagged_indices = pkl.load( infile )["kolmogorov_smirnov"]  # TODO undo hardcode

        non_flagged_box_positions = sorted(set(kdts_box_positions) - set(flagged_indices))
        flagged_box_positions = sorted(flagged_indices)

        non_flagged_box_data = [ kdts_box_data[i] for i in non_flagged_box_positions ]
        flagged_box_data = [ kdts_box_data[i] for i in flagged_box_positions ]
        
        non_flagged_box_props = box_props
        flagged_box_props = { "alpha" : 0.5, "facecolor" : "r" }

        non_flagged_kdts_boxes = kdts_ax.boxplot( non_flagged_box_data,
                                      widths = box_width,
                                      positions = non_flagged_box_positions,
                                      patch_artist = True,
                                      showfliers = True,
                                      boxprops = non_flagged_box_props,
                                      flierprops = flier_props )
        
        flagged_kdts_boxes = kdts_ax.boxplot( flagged_box_data,
                                              widths = box_width,
                                              positions = flagged_box_positions,
                                              patch_artist = True,
                                              showfliers = True,
                                              boxprops = flagged_box_props,
                                              flierprops = flier_props )

    else:
        # Create base kernel distance boxplot
        kdts_boxes = kdts_ax.boxplot( kdts_box_data,
                                      widths = box_width,
                                      positions = kdts_box_positions,
                                      patch_artist = True,
                                      showfliers = True,
                                      boxprops = box_props,
                                      flierprops = flier_props )
    


    # Read in mesh refinement block traffic data and plot, if available
    if block_traffic_data_path is not None:
        with open( block_traffic_data_path, "rb" ) as infile:
            block_traffic_data = pkl.load( infile )
        # Unpack
        mesh_refinement_rate = block_traffic_data["mesh_refinement_rate"]
        mre_to_block_traffic = block_traffic_data["mre_to_block_traffic"]
        # Copy axis
        mre_ax  = kdts_ax.twinx()
        # Get x-axis positions for block traffic data
        mre_data_positions = [ (x*mesh_refinement_rate)+x-1 for x in range( len( mre_to_block_traffic ) ) ][1:]
        # Get boxplot data
        mre_box_data = mre_to_block_traffic[1:]
        mre_data = [ np.mean(x) for x in mre_to_block_traffic ][1:]
        # Configure boxplot appearance
        mre_box_width = 0.5
        mre_box_props = { "alpha" : 0.5, "facecolor" : "r" }
        mre_flier_props = { "marker" : "*", "markersize" : 4 }
        # Create MRE block traffic line plot
        mre_plot_handle = mre_ax.plot( mre_data_positions, 
                                       mre_data,
                                       color="r",
                                       marker="o",
                                       linestyle="dashed",
                                       linewidth=2,
                                       markersize=12,
                                       label="Mesh Refinement Blocks Traffic"
                                     )
        # Configure MRE y-axis appearance
        mre_ax.set_ylabel("Number of Blocks Transferred During Mesh Refinement")
        if mre_ymax is not None:
            mre_ax.set_ylim(0, mre_ymax)
        # Compute correlation coefficients between block traffic and kernel distance
        kernel_distance_seq = []
        block_traffic_seq = []
        for i in range(len(mre_data_positions)):
            distance_data = kdts_box_data[ mre_data_positions[i] ]
            block_traffic_data = mre_box_data[i]
            kernel_distance_seq.append( np.var( distance_data ) )
            block_traffic_seq.append( np.median( block_traffic_data ) )
            #for dist,traffic in zip(distance_data, block_traffic_data):
            #    kernel_distance_seq.append(dist)
            #    block_traffic_seq.append(traffic)
        pearson_r, pearson_p = pearsonr( block_traffic_seq, kernel_distance_seq )
        spearman_r, spearman_p = spearmanr( block_traffic_seq, kernel_distance_seq )
        pearson_correlation_txt = "Pearson's r = {}, p = {}\n".format(np.round(pearson_r, 2), pearson_p)
        spearman_correlation_txt = "Spearman's ρ = {}, p = {}\n".format(np.round(spearman_r, 2), spearman_p)
        print( pearson_correlation_txt )
        print( spearman_correlation_txt )


    
     
    # Configure axes text appearance
    tick_label_fontdict = { "fontsize" : 12 } 

    # Configure x-axis appearance
    x_ticks = slice_indices
    if block_traffic_data_path is None:
        mesh_refinement_rate = 5
    x_tick_labels = [ str(x+1) if (x+1) % mesh_refinement_rate == 0 else '' for x in x_ticks ]
    kdts_ax.set_xticks( x_ticks )
    kdts_ax.set_xticklabels( x_tick_labels, rotation=0, fontdict=tick_label_fontdict )
    x_axis_padding = 5
    kdts_ax.set_xlim( -1*x_axis_padding, len(kdts_box_positions) + x_axis_padding )
    kdts_ax.set_xlabel("Slice Index")

    # Configure kernel distance time series y-axis appearance
    kdts_ax.set_ylabel("Kernel Distance (Higher == Runs Less Similar)")
    if kdts_ymax is not None:
        kdts_ax.set_ylim(0, kdts_ymax)

    # Configure title appearance
    # TODO

    # Annotate 
    # TODO

    # Configure legend appearance
    kdts_ax.legend( [ kdts_boxes["boxes"][0], mre_plot_handle[0] ], 
                    ["Kernel Distance Distrbutions", "Mesh Refinement Block Traffic"], 
                    loc="upper left" 
                  )

    # Save figure
    plt.savefig( output,
                 bbox_inches = "tight",
                 pad_inches = 0.25 )


if __name__ == "__main__":
    desc = "Script to visualize time series of kernel distances between slices of executions"
    parser = argparse.ArgumentParser(description=desc)
    parser.add_argument("kdts_data", 
                        help="Path to pickle file of kernel distance time series data")
    parser.add_argument("kernel_file", 
                        help="Path to JSON file defining which graph kernel's distance data to plot")
    parser.add_argument("-b", "--block_traffic_data",
                        help="Path to pickle file of block traffic data")
    parser.add_argument("--flagged_slices", required=False, default=None,
                        help="A list of slice indices indicating which slices have been flagged by anomaly detection and should be marked with a contrasting color. (Optional)")
    parser.add_argument("--kdts_ymax", required=False, type=int, default=None, 
                        help="Y-axis maximum for the kernel distance time series data")
    parser.add_argument("--mre_ymax", required=False, type=int, default=None,
                        help="Y-axis maximum for the mesh refinement block traffic data")
    parser.add_argument("-o", "--output", required=False, default="mini_amr_kdts.png",
                        help="Output file name")
    args = parser.parse_args()

    main( args.kdts_data, 
          args.kernel_file,
          args.block_traffic_data, 
          args.flagged_slices,
          args.kdts_ymax,
          args.mre_ymax,
          args.output
          )
