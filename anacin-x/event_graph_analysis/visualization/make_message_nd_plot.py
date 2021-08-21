#!/usr/bin/env python3

import os
import pprint
import pickle as pkl
import json
import argparse
import numpy as np
import matplotlib
#matplotlib.use('TkAgg')
import matplotlib.pyplot as plt

from scipy.stats.stats import pearsonr, spearmanr

import sys
sys.path.append(sys.path[0]+"/..")

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

def get_scatter_plot_points( idx_to_distances ):
    x_vals = []
    y_vals = []
    for i in range(len(idx_to_distances)):
        base_x_val = i
        distances = idx_to_distances[i]
        for d in distances:
            x_val = base_x_val + np.random.uniform(-0.25,0.25)
            y_val = d
            x_vals.append( x_val )
            y_vals.append( y_val )
    return x_vals, y_vals

def adjacent_values(vals, q1, q3):
    upper_adjacent_value = q3 + (q3 - q1) * 1.5
    upper_adjacent_value = np.clip(upper_adjacent_value, q3, vals[-1])

    lower_adjacent_value = q1 - (q3 - q1) * 1.5
    lower_adjacent_value = np.clip(lower_adjacent_value, vals[0], q1)
    return lower_adjacent_value, upper_adjacent_value

def main( kdts_path, pattern, output, kernel_path, nd_start, nd_iter, nd_end, nd_frac ):
    # Read in kdts data
    with open( kdts_path, "rb" ) as infile:
        slice_idx_to_data = pkl.load( infile )
    
    with open(kernel_path, "r" ) as infile:
        kernel = json.load(infile)
    
    # Unpack kernel distance time series data
    slice_indices = sorted( slice_idx_to_data.keys() )
    kernel_key = kernel_json_to_key( kernel )
    kernel_matrices = [ slice_idx_to_data[i]["kernel_distance"][kernel_key] for i in slice_indices ]
    idx_to_distances = [ flatten_distance_matrix(km) for km in kernel_matrices ]

    # Package data for scatter plot
    scatter_x_vals, scatter_y_vals = get_scatter_plot_points( idx_to_distances )

    # Package data for box-plots
    bp_positions = []
    bp_data = []
    for i in range( len(idx_to_distances) ):
        bp_positions.append( i )
        bp_data.append( idx_to_distances[i] )
    
    # Specify appearance of boxes
    box_width = 0.8
    flierprops = { "marker" : "+",
                   "markersize" : 4
                 }
    boxprops = { "alpha" : 0.5,
            "facecolor" : "tab:brown"
               } 
    whiskerprops = { "linewidth" : 3
            }
    
    # Specify appearance of scatter plot markers
    marker_size = 6
    marker_color = "b"
    alpha_value = 0.5
    
    aspect_ratio = "widescreen"
    figure_scale = 1.5
    if aspect_ratio == "widescreen":
        base_figure_size = (16, 9)
    else:
        base_figure_size = (4, 3)

    figure_size = (figure_scale*base_figure_size[0], figure_scale*base_figure_size[1] )

    fig,ax = plt.subplots( figsize=figure_size )

    # Create box plots 
    #bp = ax.boxplot( bp_data,
    #                 widths=box_width,
    #                 positions=bp_positions,
    #                 patch_artist=True,
    #                 showfliers=False,
    #                 boxprops=boxprops,
    #                 whiskerprops=whiskerprops,
    #                 flierprops=flierprops )

    #bp_quantiles = [[0.25, 0.5, 0.75] for i in range(len(bp_positions))]

    bp = ax.violinplot( bp_data, widths=box_width, positions=bp_positions, showmedians=True, showextrema=True )

    for sprops in bp['bodies']:
        #sprops.set_facecolor('#D43F3A')
        sprops.set_facecolor('tab:olive')
        sprops.set_edgecolor('black')
        sprops.set_alpha(1)

    #bp['cquantiles'].set_edgecolors('black')
    #bp['cquantiles'].set_linewidths(2.5)
    bp['cbars'].set_linewidths(2.5)
    bp['cbars'].set_edgecolors('black')
    bp['cmins'].set_linewidths(2.5)
    bp['cmins'].set_edgecolors('black')
    bp['cmaxes'].set_linewidths(2.5)
    bp['cmaxes'].set_edgecolors('black')
    bp['cmedians'].set_linewidths(3.5)
    bp['cmedians'].set_edgecolors('black')

    # Overlay actual data points on same axis
    #ax.scatter( scatter_x_vals, 
    #            scatter_y_vals,
    #            s=marker_size,
    #            c=marker_color,
    #            alpha=alpha_value)

    quartile1, medians, quartile3 = np.percentile(bp_data, [25, 50, 75], axis=1)
    #whiskers = np.array([
    #    adjacent_values(sorted_array, q1, q3)
    #    for sorted_array, q1, q3 in zip(bp_data, quartile1, quartile3)])
    #whiskers_min, whiskers_max = whiskers[:, 0], whiskers[:, 1]

    inds = np.arange(1, len(medians) + 1)
    #ax.scatter(inds, medians, marker='o', color='white', s=30, zorder=3)
    #ax.vlines(inds, quartile1, quartile3, color='k', linestyle='-', lw=5)
    #ax.vlines(inds, whiskers_min, whiskers_max, color='k', linestyle='-', lw=1)

    plt.ylim(ymin=0)

    # Plot annotation ( correlation coefficients )
    step_count = int((nd_end - nd_start)/nd_iter);
    nd_fractions = [round(nd_start + (nd_iter * step_num), 2) for step_num in range(step_count + 1)]
    #nd_fractions = [0,0.1,0.2,0.3,0.4,0.5,0.6,0.7,0.8,0.9,1]
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

    pearson_correlation_txt = "Your Pearson's r value     = {}\n".format(np.round(pearson_r, 2))
    pearson_p_txt = "It's corresponding p value = {}\n".format(pearson_p)
    spearman_correlation_txt = "Your Spearman's ρ value    = {}\n".format(np.round(spearman_r, 2))
    spearman_p_txt = "It's corresponding p value = {}\n".format(spearman_p)
    print( pearson_correlation_txt )
    print( pearson_p_txt)
    print( "\n" )
    print( spearman_correlation_txt )
    print( spearman_p_txt)

    annotation_lines = [ "Kernel Distance vs. % Non-Deterministic Receives: Correlation Coefficients\n",
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
    tick_label_fontdict = {"fontsize" : 16}
    x_tick_labels = [ str(int(100 * nd_fractions[index])) for index in range(step_count + 1)]
    #x_tick_labels = [ "0", "10", "20", "30", "40", "50", "60", "70", "80", "90", "100" ]
    x_ticks = list(range(len(x_tick_labels)))
    ax.set_xticks( x_ticks )
    ax.set_xticklabels( x_tick_labels, rotation=0, fontdict=tick_label_fontdict )
    y_ticks = list(range(0,int(max(scatter_y_vals))+11,10))
    y_tick_labels = [ str(y) for y in y_ticks ]
    ax.set_yticks( y_ticks )
    ax.set_yticklabels( y_tick_labels, rotation=0, fontdict=tick_label_fontdict )

    # Axis labels
    x_axis_label = "Percentage of Message Non-Determinism in Application"
    y_axis_label = "Kernel Distance (Higher == Runs Less Similar)"
    axis_label_fontdict = {"fontsize" : 20}
    ax.set_xlabel( x_axis_label, fontdict=axis_label_fontdict )
    ax.set_ylabel( y_axis_label, fontdict=axis_label_fontdict )

    # Plot Title
    name_dict = {
            "message_race" : "Message Race",
            "amg2013" : "AMG2013",
            "unstructured_mesh" : "Unstructured Mesh"
            }
    #if pattern == "unstructured_mesh":
        #plot_title = "Percentage of Message Non-Determinism vs. Kernel Distance - Communication Pattern: {} ({}% neighbors non-deterministically chosen )".format(name_dict[pattern], nd_frac)
    #else:
        #plot_title = "Percentage of Message Non-Determinism vs. Kernel Distance - Communication Pattern: {}".format(name_dict[pattern])
    #title_fontdict = {"fontsize" : 22}
    #plt.title( plot_title, fontdict=title_fontdict )

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
    parser.add_argument("kernel",
                        help = "Path to json file of kernel used for KDTS calculation")
    parser.add_argument("output",
                        help = "Name of output file")
    parser.add_argument("nd_start", type=float,
                        help = "The lowest percentage of non-determinism used during the ANACIN-X run.")
    parser.add_argument("nd_iter", type=float,
                        help = "The step size for the percentages of non-determinism used during the ANACIN-X run.")
    parser.add_argument("nd_end", type=float,
                        help = "The highest percentage of non-determinism used during the ANACIN-X run.")
    parser.add_argument("--nd_neighbor_fraction", type=float,
                        help="Fraction of neighbors determined non-deterministically for these runs of the unstructured mesh comm. pattern")
    args = parser.parse_args()
    main( args.data, args.comm_pattern, args.output, args.kernel, args.nd_start, args.nd_iter, args.nd_end, args.nd_neighbor_fraction )
