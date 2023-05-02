#!/usr/bin/env python3

#SBATCH -n 1
#SBATCH -n 1
#SBATCH -t 01:00:00
#SBATCH -o visualize_kernel_distance_time_series-%j.out
#SBATCH -e visualize_kernel_distance_time_series-%j.err

import os
import pprint
import pickle as pkl
import argparse
import numpy as np
import matplotlib
#matplotlib.use('TkAgg')
import matplotlib.pyplot as plt

# Needed for violin plots b/c matplotlib's is broken
import pandas as pd
import seaborn as sns

import sys
sys.path.append(".")
sys.path.append("..")
#sys.path.append("/$HOME/Src_ANACIN-X/anacin-x/event_graph_analysis/") #This needs to be fixed
sys.path.append(sys.path[0]+"/..")

from graph_kernel_postprocessing import flatten_distance_matrix
from kernel_distance_time_series_postprocessing import get_distances_seq, get_stats_seq

def make_pairwise_scatter_plot( slice_idx_to_data ):
    # Unpack kernel distance stuff
    graph_pair_to_distance_seq = {}
    slice_idx_seq = list( sorted( slice_idx_to_data.keys() ) )
    for slice_idx,data in sorted( slice_idx_to_data.items() ):
        # Get kernel distance data for this slice
        kernel_distance_data = data["kernel_distance"]
        for k,dist_mat in kernel_distance_data.items():
            # Extract all pairwise distances at this slice, for this kernel
            for i in range(len(dist_mat)):
                for j in range(len(dist_mat[0])):
                    if i > j:
                        graph_pair = (i,j)
                        distance = dist_mat[i][j]
                        if graph_pair not in graph_pair_to_distance_seq:
                            graph_pair_to_distance_seq[ graph_pair ] = [ distance ]
                        else:
                            graph_pair_to_distance_seq[ graph_pair ].append( distance )


    # Scale kernel distances
    max_dist = 0
    for distance_seq in graph_pair_to_distance_seq.values():
        max_in_seq = max( distance_seq )
        if max_in_seq > max_dist:
            max_dist = max_in_seq
    graph_pair_to_scaled_distance_seq = { gp:[ d/max_dist for d in dist_seq ] for gp,dist_seq in graph_pair_to_distance_seq.items() }

    fig,ax = plt.subplots()
    for graph_pair,distance_seq in graph_pair_to_scaled_distance_seq.items():
        graph_pair_label = str(graph_pair)
        ax.plot( slice_idx_seq, distance_seq, '-o', label=graph_pair_label, color=np.random.rand(3,) )
        #ax.plot( slice_idx_seq, distance_seq, '-o', label=graph_pair_label, color="r" )
   
    ax.legend( loc="upper left", ncol=6, fancybox=True )
    plt.show()


def make_plot(lts_to_distances):
    lts_midpoints = []
    wl_median_distances = []
    for interval,kernel_to_distance_data in lts_to_distances.items():
        lts_lower, lts_upper = interval
        midpoint = (lts_lower + lts_upper)/2
        lts_midpoints.append(midpoint)
        if "wl" in kernel_to_distance_data:
            K = kernel_to_distance_data["wl"]
            wl_distances = []
            for i in range(len(K)):
                for j in range(len(K[0])):
                    if i != j:
                        wl_distances.append(K[i][j])
            median_distance = np.median( wl_distances )
            wl_median_distances.append( median_distance )

   
    fig, ax = plt.subplots( figsize=(8,6) )

    ax.plot(lts_midpoints, wl_median_distances, color="b", marker="+", linestyle="--", linewidth=1, label="WL-Subtree")
    #ax.scatter(lts_midpoints, rw_kernel_distances, color="r", label="Rand. Walk")
    #ax.scatter(lts_midpoints, vh_kernel_distances, color="g", label="Vertex Hist")

    ax.set_xlabel("Logical Timestamp Interval Midpoint")
    ax.set_ylabel("Kernel Distance")

    plt.legend( loc="best" )

    plt.show()

    #plt.savefig("kernel_distance_time_series.png")

def make_barrier_time_series_plot( kernel_distance_data ):
    # Unpack
    timings = [] 
    kernel_to_dist_time_series = {}
    for slice_idx,data in sorted(kernel_distance_data.items()):
        timings.append( data["timings"] )
        for kernel in data["kernels"]:
            if kernel not in kernel_to_dist_time_series:
                if kernel == "eh":
                    kernel_to_dist_time_series[kernel] = [ data["kernels"][kernel] ]
                else:
                    kernel_to_dist_time_series[kernel] = [ data["kernels"][kernel][5] ]
            else:
                if kernel == "eh":
                    kernel_to_dist_time_series[kernel].append( data["kernels"][kernel] )
                else:
                    kernel_to_dist_time_series[kernel].append( data["kernels"][kernel][5] )
    

    bp_data = []
    for dist_mat in kernel_to_dist_time_series["wl"]:
        distances = []
        for i in range(len(dist_mat)):
            for j in range(len(dist_mat[0])):
                if i != j:
                    distances.append( dist_mat[i][j] )
        bp_data.append( distances )

    #indices = []
    #distances = []
    #for idx,distance_mat in idx_to_distances.items():
    #    if idx > 418:
    #        break
    #    indices.append( idx )
    #    distance_values = []
    #    for i in range(len(distance_mat)):
    #        for j in range(len(distance_mat[0])):
    #            if i != j:
    #                distance_values.append( distance_mat[i][j] )
    #    distances.append( distance_values )

    fig, ax = plt.subplots()
    flierprops = { "marker" : "+",
                   "markersize" : 1
                 }
    ax.boxplot( bp_data,
                patch_artist=True, 
                showfliers=False,
                flierprops=flierprops
              )
    plt.show()
        
def make_violin_plots( slice_idx_to_data, output_dir ):
    # Unpack kernel distance stuff
    wall_times = [] 
    kernel_to_distance_data_seq = {}
    slice_indices = list( sorted( slice_idx_to_data.keys() ) )
    for slice_idx,data in sorted( slice_idx_to_data.items() ):
        # Get bounds for wall times for this slice
        wall_time_data = data["wall_time"]
        min_wall_times = []
        max_wall_times = []
        for graph_idx in wall_time_data:
            min_wall_times.append( wall_time_data[ graph_idx ]["min_wall_time"] )
            max_wall_times.append( wall_time_data[ graph_idx ]["max_wall_time"] )
        global_min = min( min_wall_times )
        global_max = max( max_wall_times )
        wall_time_midpoint = global_min + ( ( global_max - global_min ) / 2.0 )
        #print("Slice Index: {} - min. wall-time: {}, max. wall-time: {}".format( slice_idx, global_min, global_max ))
        wall_times.append( wall_time_midpoint )
        
        # Get kernel distance data for this slice
        kernel_distance_data = data["kernel_distance"]
        for k,dist_mat in kernel_distance_data.items():
            # Extract all pairwise distances at this slice, for this kernel
            distances = []
            for i in range(len(dist_mat)):
                for j in range(len(dist_mat[0])):
                    if i > j:
                        distances.append( dist_mat[i][j] )
            if k not in kernel_to_distance_data_seq:
                kernel_to_distance_data_seq[k] = [ distances ]
            else:
                kernel_to_distance_data_seq[k].append( distances )

    fig, ax = plt.subplots()
    # Specify which kernels to plot
    #kernels_to_plot = [ ('wlst', 5, 'logical_time') ]
    kernels_to_plot = [ ('wlst', 'logical_time', 5) ]
    # Create violin plots for each kernel's time-series of kernel distance data
    label_to_plot = {}
    for kernel in kernels_to_plot:
        data = kernel_to_distance_data_seq[ kernel ]
        violin_plot_data = [ np.array(d) for d in data ]
        
        n_plots = len(violin_plot_data)

        #vp = ax.violin( data
        #                #positions=slice_indices,
        #                #showmedians=True,
        #                #showmeans=True,
        #                #showextrema=True
        #)
        axis = sns.violinplot( data=violin_plot_data  )

        #label_to_plot[ str(kernel) ] = vp
   
    ## X-axis stuff
    #if wall_time_layout:
    #    x_tick_labels_base = [ str(round(wt,3)) for wt in wall_times ]
    #    x_axis_label = "Wall Time (s)"
    #    x_tick_labels = []
    #    for idx,label in enumerate(x_tick_labels_base):
    #        if idx == 0 or idx == len(x_tick_labels_base)-1:
    #            x_tick_labels.append( label )
    #        else:
    #            x_tick_labels.append( "" )
    #else:
    #    x_tick_labels_base = [ str(i) for i in range(n_plots) ]
    #    x_axis_label = "Slice Index"
    ## Select subset of x-tick labels so axis isn't too crowded
    #ax.set_xticklabels( x_tick_labels_base, rotation=45 )
    #ax.set_xlabel( x_axis_label )

    ## Y-axis stuff
    #y_axis_label = "Kernel Distance (Higher == Runs Less Similar)"
    #ax.set_ylabel( y_axis_label )

    ## Legend stuff
    #ax.legend( [ label_to_plot[k]["es"][0] for k in sorted(label_to_plot.keys()) ], list(sorted(label_to_plot.keys())), loc="best" )

    ## Plot title
    #plot_title = "Kernel Distance Time Series"
    #plt.title( plot_title )

    plt.show()
    #This is incinclusive for now
    kdts_save_path = output_dir + "/kdts.png" if output_dir != "" else "kdts.png"
    #plt.savefig( "kdts.png", 
    plt.savefig( kdts_save_path, 
                 bbox_inches="tight",
                 transparent=False,
                 pad_inches=0.05,
                 dpi=300 )





def make_scatter_plot( slice_idx_to_data, slice_idx_lower, slice_idx_upper, stats , output_dir):
    # Select slice indices
    all_slice_indices = sorted( slice_idx_to_data.keys() )
    if slice_idx_lower is not None and slice_idx_upper is not None:
        slice_indices = all_slice_indices[ slice_idx_lower : slice_idx_upper+1 ]
    else:
        slice_indices = all_slice_indices

    kernel = ('wlst','logical_time', 5)
    idx_to_distances = { k:flatten_distance_matrix(v["kernel_distance"][kernel]) for k,v in slice_idx_to_data.items() }

    x_vals = []
    y_vals = []
    for slice_idx,distances in idx_to_distances.items():
        base_x_val = slice_idx
        for d in distances:
            x_val = base_x_val + np.random.uniform(-0.25,0.25)
            y_val = d
            x_vals.append( x_val )
            y_vals.append( y_val )

    fig,ax = plt.subplots()
    ax.scatter( x_vals, y_vals )

    x_axis_label = "% Messages Non-Deterministic"
    x_tick_labels = [ "0", "20", "30", "40", "50", "60", "70", "80", "90", "100" ]
    x_ticks = list(range(len(x_tick_labels)))
    ax.set_xticks( x_ticks )
    ax.set_xticklabels( x_tick_labels, rotation=45 )
    ax.set_xlabel( x_axis_label )

    # Y-axis stuff
    y_axis_label = "Kernel Distance (Higher == Runs Less Similar)"
    ax.set_ylabel( y_axis_label )

    # Plot title
    plot_title = "Fraction of Messages Non-Deterministic vs. Kernel Distance"
    plt.title( plot_title )

    plt.show()
    #This is inconclusive for now
    kdts_save_path = output_dir + "/kdts.png" if output_dir != "" else "kdts.png"
    #plt.savefig( "kdts.png", 
    plt.savefig( kdts_save_path, 
                 bbox_inches="tight",
                 transparent=False,
                 pad_inches=0.05,
                 dpi=300 )

def get_plot_element_positions( slice_idx_to_data, slice_idx_lower, slice_idx_upper, slice_indices, wall_time_layout ):
    requested_slices = get_requested_slices( slice_idx_to_data, slice_idx_lower, slice_idx_upper, slice_indices )




"""
Determines which slices' data will be plotted.
"""
def get_requested_slices( slice_idx_to_data, slice_idx_lower, slice_idx_upper, slice_indices ):
    # Case 1: All slices
    if slice_idx_lower is None and slice_idx_upper is None and slice_indices is None:
        requested_slice_indices = sorted( slice_idx_to_data.keys() )
    # Case 2: Contiguous range of slices
    elif slice_idx_lower is not None and slice_idx_upper is not None and slice_indices is None:
        requested_slice_indices = list( range( slice_idx_lower, slice_idx_upper+1 ) )
    # Case 3: User-defined set of slices
    else:
        requested_slice_indices = slice_indices
    return requested_slice_indices




def make_box_plots( slice_idx_to_data, slice_idx_lower, slice_idx_upper, wall_time_layout, application_events, output_dir ):
    # Unpack kernel distance stuff
    wall_times = [] 
    kernel_to_distance_data_seq = {}
    

    slice_indices = sorted( slice_idx_to_data.keys() )
    if slice_idx_lower is not None and slice_idx_upper is not None:
        slice_indices = list( filter( lambda i : i >= slice_idx_lower and i <= slice_idx_upper, slice_indices ) )
    

    #for slice_idx,data in sorted( slice_idx_to_data.items() ):
    for slice_idx in slice_indices:
        data = slice_idx_to_data[ slice_idx ]
        # Get bounds for wall times for this slice
        wall_time_data = data["wall_time"]
        min_wall_times = []
        max_wall_times = []
        for graph_idx in wall_time_data:
            min_wall_times.append( wall_time_data[ graph_idx ]["min_wall_time"] )
            max_wall_times.append( wall_time_data[ graph_idx ]["max_wall_time"] )
        global_min = min( min_wall_times )
        global_max = max( max_wall_times )
        wall_time_midpoint = global_min + ( ( global_max - global_min ) / 2.0 )
        #print("Slice Index: {} - min. wall-time: {}, max. wall-time: {}".format( slice_idx, global_min, global_max ))
        wall_times.append( wall_time_midpoint )
        
        # Get kernel distance data for this slice
        kernel_distance_data = data["kernel_distance"]
        for k,dist_mat in kernel_distance_data.items():
            # Extract all pairwise distances at this slice, for this kernel
            distances = []
            for i in range(len(dist_mat)):
                for j in range(len(dist_mat[0])):
                    if i > j:
                        distances.append( dist_mat[i][j] )
            if k not in kernel_to_distance_data_seq:
                kernel_to_distance_data_seq[k] = [ distances ]
            else:
                kernel_to_distance_data_seq[k].append( distances )

    fig, ax = plt.subplots()
    fig.set_size_inches( 18, 9 )
   
    # Track maximum y-value of data so we know how tall to make application 
    # event lines/boxes
    y_data_max = 0
    
    # Specify which kernels to plot
    #kernels_to_plot = [ ('wlst', 5, 'logical_time') ]
    kernels_to_plot = [ ('wlst','logical_time', 5) ]
    #kernels_to_plot = [ ('eh', 'logical_latency') ]

    # Specify appearance of boxes
    flierprops = { "marker" : "+",
                   "markersize" : 1
                 }
    # Create box plots for each kernel's time-series of kernel distance data
    label_to_boxplot = {}
    for kernel in kernels_to_plot:
        bp_data = kernel_to_distance_data_seq[ kernel ]

        ## Filter boxes to look at 
        ##bp_data = [ bp_data[i] if i % 10 == 0 else None for i in range(len(bp_data)) ]
        #bp_data = [ bp_data[i] if i < 100 else None for i in range(len(bp_data)) ]
        #bp_data = list( filter( lambda x: x is not None, bp_data ) )
        ##positions = [ i if i % 10 == 0 else None for i in slice_indices ]
        #positions = [ i if i < 100 else None for i in slice_indices ]
        #positions = list( filter( lambda x: x is not None, positions ) )
        positions = slice_indices

        # Flag distance sets of median distance was increasing
        colors = []
        for idx in range(1,len(bp_data)):
            prev_dists = bp_data[ idx-1 ]
            curr_dists = bp_data[ idx ]
            prev_median = np.median( prev_dists )
            curr_median = np.median( curr_dists )

            
        box_width = 0.5

        n_boxes = len(bp_data)
        y_data_max = max( y_data_max, max( [ max(box_data) for box_data in bp_data] ) )
        # If we're plotting the boxes at wall-time positions, we need to specify
        # box width b/c the default doesn't handle it well and we get lots of 
        # overlap
        if wall_time_layout:
            bp_positions = wall_times
            box_width = 2.0
            bp = ax.boxplot( bp_data, 
                             widths=box_width,
                             positions=wall_times,
                             patch_artist=True, 
                             showfliers=False,
                             flierprops=flierprops,
                           )
        # Otherwise just plot them at standard positions and use the default 
        # width formula
        else:
            bp = ax.boxplot( bp_data, 
                             widths=box_width,
                             positions=positions,
                             patch_artist=True, 
                             showfliers=False,
                             flierprops=flierprops,
                           )
        label_to_boxplot[ str(kernel) ] = bp
   
    if application_events is not None:
        for event,timings in event_to_timings.items():
            event_start = timings["start"]
            event_stop = timings["stop"]
            event_midpoint = event_start + ( ( event_stop - event_start ) / 2.0 )
            #print("Refinement step: {} spans {}s to {}s".format(event, event_start, event_stop ))
            ax.axvline( event_midpoint, ymin=0, ymax=y_data_max, color="r", linewidth=1.0, label="miniAMR Refinement Step" )

    # X-axis stuff
    if wall_time_layout:
        x_tick_labels_base = [ str(round(wt,3)) for wt in wall_times ]
        x_axis_label = "Wall Time (s)"
        x_tick_labels = []
        for idx,label in enumerate(x_tick_labels_base):
            if idx == 0 or idx == len(x_tick_labels_base)-1:
                x_tick_labels.append( label )
            else:
                x_tick_labels.append( "" )
    else:
        x_tick_labels_base = [ str(i) for i in range(n_boxes) ]
        x_axis_label = "Slice Index"
        #x_axis_label = "% Messages Non-Deterministic"
        #x_tick_labels = [ "0", "20", "30", "40", "50", "60", "70", "80", "90", "100" ]
        #x_tick_labels = []
        #for idx,label in enumerate(x_tick_labels_base):
        #    if idx == 0 or idx == len(x_tick_labels_base)-1:
        #        x_tick_labels.append( label )
        #    else:
        #        if idx % 10 == 0:
        #            x_tick_labels.append( label )
        #        else:
        #            x_tick_labels.append( "" )
    # Select subset of x-tick labels so axis isn't too crowded
    #ax.set_xticklabels( x_tick_labels, rotation=45 )
    ax.set_xlabel( x_axis_label )

    # Y-axis stuff
    y_axis_label = "Kernel Distance (Higher == Runs Less Similar)"
    ax.set_ylabel( y_axis_label )

    #ax.set_ylim(0, 700)

    # Legend stuff
    #ax.legend( [ label_to_boxplot[k]["boxes"][0] for k in sorted(label_to_boxplot.keys()) ], list(sorted(label_to_boxplot.keys())), loc="best" )

    # Plot title
    plot_title = "Kernel Distance Time Series"
    plt.title( plot_title )

    plt.show()
    kdts_save_path = output_dir + "/kdts.png" if output_dir != "" else "kdts.png"
    #plt.savefig( "kdts.png", 
    plt.savefig( kdts_save_path, 
                 bbox_inches="tight",
                 transparent=False,
                 pad_inches=0.05,
                 dpi=300 )




def main( kdts_path, plot_type, slice_idx_lower, slice_idx_upper, flagged_slices, wall_time_layout, application_events, output_dir ):

    # Read in kdts data
    with open( kdts_path, "rb" ) as infile:
        slice_idx_to_data = pkl.load( infile )

    # if available, load and unpack application-level events
    if application_events is not None:
        with open( application_events, "rb" ) as infile:
            event_to_timings = pkl.load( infile )

    if plot_type == "box":
        make_box_plots( slice_idx_to_data, slice_idx_lower, slice_idx_upper, wall_time_layout, application_events, output_dir )

    elif plot_type == "scatter":
        make_scatter_plot( slice_idx_to_data, slice_idx_lower, slice_idx_upper, ["min", "max", "median"], output_dir )

    elif plot_type == "violin":
        make_violin_plots( slice_idx_to_data, output_dir )


if __name__ == "__main__":
    desc = "Script to visualize time series of kernel distances between slices of executions"
    parser = argparse.ArgumentParser(description=desc)
    parser.add_argument("data", 
                        help="Path to pickle file of kernel distance time series data")
    parser.add_argument("--plot_type", 
                        help="Specify which kind of visualization to create. Options: box, scatter, violin")
    parser.add_argument("-l", "--lower", required=False, default=None, type=int,
                        help="Lower bound (inclusive) of slice indices for which to plot data")
    parser.add_argument("-u", "--upper", required=False, default=None, type=int,
                        help="Upper bound (inclusive) of slice indices for which to plot data")
    parser.add_argument("--flagged_slices", required=False, default=None,
                        help="A list of slice indices indicating which slices have been flagged by anomaly detection and should be marked with a contrasting color. (Optional)")
    parser.add_argument("-w", "--wall_time_layout", action="store_true", default=False,
                        help="If enabled, place the kernel distance boxplots for each slice on the x-axis based on the wall-time of the slice")
    parser.add_argument("-a", "--application_events", required=False,
                        help="Path to pickle file of supplementary application-specific event data")
    parser.add_argument("-o", "--output_dir", required=False, default="",
                        help="Directory to store visualization output.")
    args = parser.parse_args()

    main( args.data, 
          args.plot_type, 
          args.lower, 
          args.upper, 
          args.flagged_slices,
          args.wall_time_layout, 
          args.application_events,
          args.output_dir)

