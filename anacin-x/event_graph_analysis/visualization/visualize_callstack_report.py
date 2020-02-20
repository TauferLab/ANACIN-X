#!/usr/bin/env python3
import sys
sys.path.append("../")
sys.path.append("./")

import argparse
import igraph
import re
import pprint
import matplotlib
matplotlib.use('TkAgg')
import matplotlib.pyplot as plt


def get_callstack_and_count_from_line( line ):
    callstack,count = line.split(":")
    callstack = tuple( [ x.strip() for x in callstack.split("-->") ] )
    count = int(count)
    return callstack ,count

def get_location_from_line( line ):
    components = line.split(",")
    fn, fn_file, fn_line = [ x.split(":")[-1].strip() for x in components ]
    fn_line = int( fn_line )
    return fn, fn_file, fn_line

def parse_report( report_path ):
    with open( report_path, "r" ) as infile:
        lines = infile.readlines()
    count_line_pattern = re.compile("^main( --> \w+)+ : \d+$")
    fn_loc_pattern = re.compile("^Function: \w+, File: \w+\.\w, Line Number: \d+$")
    callstack_to_count = {}
    fn_to_location = {}
    for line in lines:
        if count_line_pattern.match( line ):
            callstack,count = get_callstack_and_count_from_line( line )
            callstack_to_count[ callstack ] = count
        elif fn_loc_pattern.match( line ):
            fn, fn_file, fn_line = get_location_from_line( line )
            fn_to_location[ fn ] = { "file": fn_file, "line": fn_line }
    return callstack_to_count, fn_to_location 


def make_callstack_frequency_bar_plot( callstack_to_count, y_axis="normalized" ):
    fig, ax = plt.subplots()
    spacing_factor = 20
    bar_positions = [ x*spacing_factor for x in range(len(sorted(callstack_to_count))) ]
    bar_heights = sorted(callstack_to_count.values())
    bar_width = 0.4*spacing_factor
    ax.bar( bar_positions, bar_heights, width=bar_width )  
    # Set y-axis limit
    if y_axis == "normalized":
        ax.set_ylim(0, 1.0)
    # Annotate x-axis
    x_axis_label = "Call-Stack"
    x_tick_labels = []
    for callstack in sorted(callstack_to_count.keys()):
        callstack_str = ""
        for idx,fn in enumerate(callstack):
            callstack_str += fn
            if idx != len(callstack)-1:
                callstack_str += "\n"
        x_tick_labels.append( callstack_str )
    ax.set_xlabel( x_axis_label )
    ax.set_xticks( bar_positions )
    ax.set_xticklabels( x_tick_labels, rotation=0, fontsize=8 )
    # Annotate y-axis
    y_axis_label = "Frequency"
    ax.set_ylabel( y_axis_label )
    plt.show()


def normalize_counts( callstack_to_count ):
    total_n_calls = sum( callstack_to_count.values() )
    return { k:v/total_n_calls for k,v in callstack_to_count.items() }


#def make_call_graph_plot( callstack_to_count, global_callstack_distribution ):
    # Construct base call-graph


def get_unique_calls( callstack_to_count ):
    calls = set()
    for cs in callstack_to_count:
        for c in cs:
            calls.add( c )
    return list(calls)

def make_call_graph( callstack_to_count ):
    # First determine the set of unique function calls present in all callstacks
    # Each unique function call is represented by vertex
    calls = get_unique_calls( callstack_to_count )
    n_vertices = len( calls )
    g = igraph.Graph( n_vertices, directed=True )
    # Label vertices
    g.vs[:]["fn"] = calls
    # Build mapping from function call names to vertex IDs so we can look up
    # how to define edges in next step
    call_to_vid = {}
    for v in g.vs[:]:
        call_to_vid[ v["fn"] ] = v.index
    # Iterate through callstacks and add weighted edges representing 
    # caller-callee relationships and their frequency
    edges = []
    edge_set = set()
    weights = []
    for cs,count in callstack_to_count.items():
        for i in range(1,len(cs)):
            caller = cs[i-1]
            callee = cs[i]
            caller_vid = call_to_vid[ caller ]
            callee_vid = call_to_vid[ callee ]
            edge = ( caller_vid, callee_vid )
            # Only add edge if it is non-duplicate
            if edge not in edge_set:
                edge_set.add( edge )
                edges.append( edge )
                weights.append( count )
    g.add_edges( edges )
    g.es[:]["freq"] = weights

    #for e in g.es[:]:
    #    print("{} --> {} : freq={}".format(e.source, e.target, e["freq"]))
    #for v in g.vs[:]:
    #    print(v)
   
    # Set vertex label distance
    vertex_label_distances = [ 1 ] * n_vertices
    max_f = max( g.es[:]["freq"] )
    normalized_freqs = [ f/max_f for f in g.es[:]["freq"] ]
    edge_width_scale = 2
    edge_widths = [ f*edge_width_scale for f in normalized_freqs ]

    igraph.plot( g, 
                 vertex_label=g.vs[:]["fn"],
                 vertex_label_dist=vertex_label_distances,
                 edge_width=edge_widths
               )
    
    


def main( report_path, plot_type, y_axis, global_callstack_distribution ):
    callstack_to_count, fn_to_location = parse_report( report_path )
    
    g = make_call_graph( callstack_to_count )

    #if y_axis == "normalized":
    #    callstack_to_freq = normalize_counts( callstack_to_count )
    #    make_callstack_frequency_bar_plot( callstack_to_freq )
    #elif y_axis == "raw":
    #    make_callstack_frequency_bar_plot( callstack_to_count, y_axis=y_axis )

if __name__ == "__main__":
    desc = ""
    parser = argparse.ArgumentParser(description=desc)
    parser.add_argument("report_path", 
                        help="")
    parser.add_argument("-p", "--plot_type", 
                        help="Type of plot to generate. Options: bar_chart, call_graph ")
    parser.add_argument("-y", "--y_axis", required=False, default="normalized",
                        help="")
    parser.add_argument("--global_callstack_distribution", required=False, default=None,
                        help="Path to counts of all callstacks across all slices from all runs. Required if --plot_type is \"call_graph\"")
    args = parser.parse_args()

    main( args.report_path, args.plot_type, args.y_axis, args.global_callstack_distribution )
