#!/usr/bin/env python3

#SBATCH -n 1
#SBATCH -n 1
#SBATCH -t 01:00:00
#SBATCH -o make_mini_amr_kdts_plot-%j.out
#SBATCH -e make_mini_amr_kdts_plot-%j.err

import argparse
import pickle as pkl
import json

import numpy as np

import matplotlib
matplotlib.use('TkAgg')
import matplotlib.pyplot as plt

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


def main( kdts_data_path, kernel_file_path, block_traffic_data_path=None, flagged_slices=None ):

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
        mre_data_positions = [ (x*mesh_refinement_rate)+x-1 for x in range( len( mre_to_block_traffic ) ) ]
        # Get boxplot data
        mre_box_data = mre_to_block_traffic
        mre_data = [ np.mean(x) for x in mre_to_block_traffic ]
        # Configure boxplot appearance
        mre_box_width = 0.5
        mre_box_props = { "alpha" : 0.5, "facecolor" : "r" }
        mre_flier_props = { "marker" : "*", "markersize" : 4 }
        # Create MRE block traffic line plot
        mre_ax.plot( mre_data_positions, 
                     mre_data,
                     color="r",
                     marker="o",
                     linestyle="dashed",
                     linewidth=2,
                     markersize=12 )
        # Configure MRE y-axis appearance
        mre_ax.set_ylabel("Number of Blocks Transferred")

     
    # Configure axes text appearance
    tick_label_fontdict = { "fontsize" : 12 } 

    # Configure x-axis appearance
    x_ticks = slice_indices
    x_tick_labels = [ str(x+1) if (x+1) % mesh_refinement_rate == 0 else '' for x in x_ticks ]
    kdts_ax.set_xticks( x_ticks )
    kdts_ax.set_xticklabels( x_tick_labels, rotation=0, fontdict=tick_label_fontdict )
    kdts_ax.set_xlabel("Slice Index")

    # Configure kernel distance time series y-axis appearance
    kdts_ax.set_ylabel("Kernel Distance (Higher == Runs Less Similar)")

    # Configure title appearance
    # TODO

    # Annotate 
    # TODO

    # Save figure
    plt.savefig( "mini_amr_kdts_lb_2.png",
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
    args = parser.parse_args()

    main( args.kdts_data, 
          args.kernel_file,
          args.block_traffic_data, 
          args.flagged_slices )
