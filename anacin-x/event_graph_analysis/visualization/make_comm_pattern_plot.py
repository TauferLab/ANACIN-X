#!/usr/bin/env python3

import os
import pprint
import pickle as pkl
import json
import argparse
import numpy as np
import matplotlib
matplotlib.use('TkAgg')
import matplotlib.pyplot as plt

from scipy.stats.stats import pearsonr, spearmanr

import sys
sys.path.append(".")
sys.path.append("..")
sys.path.append("/g/g12/chapp1/ANACIN-X/anacin-x/event_graph_analysis/")
sys.path.append("/g/g12/chapp1/ANACIN-X/anacin-x/event_graph_analysis/visualization/")

from graph_kernel_postprocessing import flatten_distance_matrix
from kernel_distance_time_series_postprocessing import get_distances_seq


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


def get_scatter_plot_points( kernel_distances ):
    x_vals = []
    y_vals = []
    for i in range(len(kernel_distances)):
        base_x_val = i
        distance_set = kernel_distances[i]
        for d in distance_set:
            x_val = base_x_val + np.random.uniform(-0.25, 0.25)
            y_val = d
            x_vals.append( x_val )
            y_vals.append( y_val )
    return x_vals, y_vals


def main( kdts_path, kernel_path, pattern, ymax ):
    
    # Load kernel distance time series 
    with open( kdts_path, "rb" ) as infile:
        slice_idx_to_data = pkl.load( infile )

    # Load kernel definition
    with open( kernel_path, "r" ) as infile:
        kernel = json.load(infile)

    # Unpack kernel distance time series data
    slice_indices = sorted( slice_idx_to_data.keys() )
    kernel_key = kernel_json_to_key( kernel )
    kernel_matrices = [ slice_idx_to_data[i]["kernel_distance"][kernel_key] for i in slice_indices ]
    kernel_distances = [ flatten_distance_matrix(km) for km in kernel_matrices ]

    # Get scatter plot points
    scatter_x_vals, scatter_y_vals = get_scatter_plot_points( kernel_distances )

    # Package data for box plots
    bp_positions = []
    bp_data = []
    for i in range(len(kernel_distances)):
        bp_positions.append(i)
        bp_data.append(kernel_distances[i])
    
    # Specify appearance of boxes
    box_width = 0.5
    flierprops = { "marker" : "+",
                   "markersize" : 4
                 }
    boxprops = { "alpha" : 1.0,
                 "linewidth" : 3,
                 "color" : "black"
               } 
    
    # Specify appearance of scatter plot markers
    marker_size = 1
    marker_color = "lightblue"

    aspect_ratio = "widescreen"
    figure_scale = 1.5
    if aspect_ratio == "widescreen":
        base_figure_size = (16, 9)
    else:
        base_figure_size = (4, 3)

    figure_size = (figure_scale*base_figure_size[0], figure_scale*base_figure_size[1] )

    fig,ax = plt.subplots( figsize=figure_size )
    
    # Create box plots 
    bp = ax.boxplot( bp_data,
                     widths=box_width,
                     positions=bp_positions,
                     patch_artist=True,
                     showfliers=False,
                     boxprops=boxprops,
                     flierprops=flierprops )
    
    # Overlay actual data points on same axis
    ax.scatter( scatter_x_vals, 
                scatter_y_vals,
                s=marker_size,
                c=marker_color
                )
    
    # Plot annotation ( correlation coefficients )
    nd_fractions = [ 0, 0.1, 0.2, 0.3, 0.4, 0.5, 0.6, 0.7, 0.8, 0.9, 1.0 ]
    nd_fraction_seq = []
    dist_seq = []
    for i in range( len( nd_fractions ) ):
        for d in kernel_distances[i]:
            nd_fraction_seq.append( nd_fractions[i] )
            dist_seq.append( d )
    pearson_r, pearson_p = pearsonr( nd_fraction_seq, dist_seq )
    spearman_r, spearman_p = spearmanr( nd_fraction_seq, dist_seq )
    pearson_correlation_txt = "Pearson's r = {}, p = {}\n".format(np.round(pearson_r, 2), pearson_p)
    spearman_correlation_txt = "Spearman's rho = {}, p = {}\n".format(np.round(spearman_r, 2), spearman_p)
    print( pearson_correlation_txt )
    print( spearman_correlation_txt )
    
    annotation_lines = [ "Correlation Coefficients\n",
                         pearson_correlation_txt,
                         spearman_correlation_txt
                       ]
    
    annotation_txt = "".join(annotation_lines)
    annotation_font_size = 18
    ax.annotate( annotation_txt, 
                 xy=(0.45, 0.25), 
                 xycoords='axes fraction',
                 fontsize=annotation_font_size,
                 bbox=dict(boxstyle="square, pad=1", fc="w")
               )
    
    # Shared axis properties
    tick_label_fontdict = {"fontsize" : 18}

    # X-axis properties
    x_tick_labels = [ "0", "10", "20", "30", "40", "50", "60", "70", "80", "90", "100" ]
    x_tick_labels = [ x + "%" for x in x_tick_labels ]
    x_ticks = list(range(len(x_tick_labels)))
    ax.set_xticks( x_ticks )
    ax.set_xticklabels( x_tick_labels, rotation=0, fontdict=tick_label_fontdict )
    
    # Y-axis properties
    y_ticks = [ 0, 10, 20, 30, 40, 50, 60, 70 ]
    y_tick_labels = [ str(y) for y in y_ticks ]
    ax.set_yticks( y_ticks )
    ax.set_yticklabels( y_tick_labels, rotation=0, fontdict=tick_label_fontdict )
    if ymax is not None:
        ax.ylim(0, ymax)

    # Axis labels
    x_axis_label = "Percentage of Wildcard Receives (i.e., using MPI_ANY_SOURCE)"
    y_axis_label = "Kernel Distance (Higher == Runs Less Similar)"
    axis_label_fontdict = {"fontsize" : 18}
    ax.set_xlabel( x_axis_label, fontdict=axis_label_fontdict )
    ax.set_ylabel( y_axis_label, fontdict=axis_label_fontdict )

    # Annotate plot
    pattern_to_nice_name = { "message_race"      : "Message Race",
                             "amg2013"           : "AMG2013",
                             "mini_mcb_grid"     : "Mini-MCB Grid",
                             "unstructured_mesh" : "Unstructured Mesh"
                           }
    if pattern is not None:
        plot_title = "Percentage of Wildcard Receives vs. Kernel Distance - Communication Pattern: {}".format(pattern_to_nice_name[pattern])
    else:
        plot_title = "Percentage of Wildcard Receives vs. Kernel Distance"
    title_fontdict = {"fontsize" : 20}
    plt.title( plot_title, fontdict=title_fontdict )
    
    if pattern is not None:
        save_path = "nd_fraction_vs_kernel_distance_{}.png".format(pattern)
    else:
        save_path = "nd_fraction_vs_kernel_distance.png"
    plt.savefig( save_path,
                 bbox_inches="tight",
                 pad_inches=0.25,
                 dpi=600
               )

if __name__ == "__main__":
    desc = "Make box plot of ND fraction vs. kernel distance for comm. pattern"
    parser = argparse.ArgumentParser(description=desc)
    parser.add_argument("data", 
                        help="Path to pickle file of kernel distance time series data")
    parser.add_argument("-k", "--kernel", 
                        help="Path to JSON defining the graph kernel corresponding to the kernel distances to plot")
    parser.add_argument("-p", "--pattern", required=False, default=None,
                        help="Name of communication pattern")
    parser.add_argument("--ymax", required=False, default=None,
                        help="Y-axis maximum")
    args = parser.parse_args()
    main( args.data, args.kernel, args.pattern, args.ymax )
