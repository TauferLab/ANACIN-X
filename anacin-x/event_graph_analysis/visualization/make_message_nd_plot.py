#!/usr/bin/env python3

import os
import pprint
import pickle as pkl
import argparse
import numpy as np
import matplotlib
#matplotlib.use('TkAgg')
import matplotlib.pyplot as plt

from scipy.stats.stats import pearsonr, spearmanr

import sys
sys.path.append(sys.path[0]+"/..")
sys.path.append(".")
sys.path.append("..")
#sys.path.append("/g/g12/chapp1/ANACIN-X/anacin-x/event_graph_analysis/")
#sys.path.append("/g/g12/chapp1/ANACIN-X/anacin-x/event_graph_analysis/visualization/")
#sys.path.append("/$HOME/Src_ANACIN-X/anacin-x/event_graph_analysis/")
#sys.path.append("/$HOME/Src_ANACIN-X/anacin-x/event_graph_analysis/visualization/")

print(sys.path[0])

from graph_kernel_postprocessing import flatten_distance_matrix
from kernel_distance_time_series_postprocessing import get_distances_seq

def get_scatter_plot_points( idx_to_distances ):
    x_vals = []
    y_vals = []
    for slice_idx,distances in idx_to_distances.items():
        base_x_val = slice_idx
        for d in distances:
            x_val = base_x_val + np.random.uniform(-0.25,0.25)
            y_val = d
            x_vals.append( x_val )
            y_vals.append( y_val )
    return x_vals, y_vals

def main( kdts_path, pattern, output, nd_frac ):
    # Read in kdts data
    with open( kdts_path, "rb" ) as infile:
        slice_idx_to_data = pkl.load( infile )
    
    kernel = ('wlst','logical_time', 5)
    idx_to_distances = { k:flatten_distance_matrix(v["kernel_distance"][kernel]) for k,v in slice_idx_to_data.items() }

    # Package data for scatter plot
    scatter_x_vals, scatter_y_vals = get_scatter_plot_points( idx_to_distances )

    # Package data for box-plots
    bp_positions = []
    bp_data = []
    for idx,distances in sorted( idx_to_distances.items() ):
        bp_positions.append( idx )
        bp_data.append( distances )
    
    # Specify appearance of boxes
    box_width = 0.5
    flierprops = { "marker" : "+",
                   "markersize" : 4
                 }
    boxprops = { "alpha" : 0.25
               } 
    
    # Specify appearance of scatter plot markers
    marker_size = 6
    
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
                s=marker_size)
   
    # Plot annotation ( correlation coefficients )
    nd_fractions = [0,0.1,0.2,0.3,0.4,0.5,0.6,0.7,0.8,0.9,1]
    nd_fraction_seq = []
    dist_seq = []
    for i in range( len( nd_fractions ) ):
        for d in idx_to_distances[i]:
            nd_fraction_seq.append( nd_fractions[i] )
            dist_seq.append( d )
    pearson_r, pearson_p = pearsonr( nd_fraction_seq, dist_seq )
    spearman_r, spearman_p = spearmanr( nd_fraction_seq, dist_seq )
    #pearson_correlation_txt = "Kernel distance vs. % ND → Pearson-R = {}, p = {}".format(np.round(pearson_r, 2), pearson_p)
    #spearman_correlation_txt = "Kernel distance vs. % ND → Spearman-R = {}, p = {}".format(np.round(spearman_r, 2), spearman_p)

    pearson_correlation_txt = "Pearson's r = {}, p = {}\n".format(np.round(pearson_r, 2), pearson_p)
    spearman_correlation_txt = "Spearman's ρ = {}, p = {}\n".format(np.round(spearman_r, 2), spearman_p)
    print( pearson_correlation_txt )
    print( spearman_correlation_txt )

    annotation_lines = [ "Kernel Distance vs. % Wildcard Receives: Correlation Coefficients\n",
                         #"=================================================================\n",
                         pearson_correlation_txt,
                         spearman_correlation_txt
                       ]
    
    annotation_txt = "".join(annotation_lines)
    annotation_font_size = 18
    #ax.annotate( annotation_txt, 
    #             xy=(0.55, 0.25), 
    #             xycoords='axes fraction',
    #             fontsize=annotation_font_size,
    #             bbox=dict(boxstyle="square, pad=1", fc="w")
    #           )

    # Tick labels
    tick_label_fontdict = {"fontsize" : 12}
    x_tick_labels = [ "0", "10", "20", "30", "40", "50", "60", "70", "80", "90", "100" ]
    x_ticks = list(range(len(x_tick_labels)))
    ax.set_xticks( x_ticks )
    ax.set_xticklabels( x_tick_labels, rotation=0, fontdict=tick_label_fontdict )
    print(scatter_y_vals)
    y_ticks = list(range(0,int(max(scatter_y_vals))+11,10))
    y_tick_labels = [ str(y) for y in y_ticks ]
    ax.set_yticks( y_ticks )
    ax.set_yticklabels( y_tick_labels, rotation=0, fontdict=tick_label_fontdict )

    # Axis labels
    x_axis_label = "Percentage of Wildcard Receives (i.e., using MPI_ANY_SOURCE)"
    y_axis_label = "Kernel Distance (Higher == Runs Less Similar)"
    axis_label_fontdict = {"fontsize" : 18}
    ax.set_xlabel( x_axis_label, fontdict=axis_label_fontdict )
    ax.set_ylabel( y_axis_label, fontdict=axis_label_fontdict )

    # Plot Title
    name_dict = {
            "message_race" : "Message Race",
            "amg2013" : "AMG2013",
            "unstructured_mesh" : "Unstructured Mesh"
            }
    if pattern == "unstructured_mesh":
        plot_title = "Percentage of Wildcard Receives vs. Kernel Distance - Communication Pattern: {} ({}% neighbors non-deterministically chosen )".format(name_dict[pattern], nd_frac)
    else:
        plot_title = "Percentage of Wildcard Receives vs. Kernel Distance - Communication Pattern: {}".format(name_dict[pattern])
    title_fontdict = {"fontsize" : 20}
    plt.title( plot_title, fontdict=title_fontdict )

    #plt.show()
    plt.savefig( "{}.png".format(output),
                 bbox_inches="tight",
                 pad_inches=0.25
               )

if __name__ == "__main__":
    desc = "Generates figure showing naive reduce example"
    parser = argparse.ArgumentParser(description=desc)
    parser.add_argument("data", 
                        help="Path to pickle file of kernel distance time series data")
    parser.add_argument("comm_pattern",
                        help = "Name of visualized communication pattern")
    parser.add_argument("output",
                        help = "Name of output file")
    parser.add_argument("--nd_neighbor_fraction", type=float,
                        help="Fraction of neighbors determined non-deterministically for these runs of the unstructured mesh comm. pattern")
    args = parser.parse_args()
    main( args.data, args.comm_pattern, args.output, args.nd_neighbor_fraction )
