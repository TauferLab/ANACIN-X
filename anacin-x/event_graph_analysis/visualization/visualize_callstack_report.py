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


def main( report_path, y_axis ):
    callstack_to_count, fn_to_location = parse_report( report_path )
    if y_axis == "normalized":
        callstack_to_freq = normalize_counts( callstack_to_count )
        make_callstack_frequency_bar_plot( callstack_to_freq )
    elif y_axis == "raw":
        make_callstack_frequency_bar_plot( callstack_to_count, y_axis=y_axis )

if __name__ == "__main__":
    desc = ""
    parser = argparse.ArgumentParser(description=desc)
    parser.add_argument("report_path", 
                        help="")
    parser.add_argument("-y", "--y_axis", required=False, default="normalized",
                        help="")
    args = parser.parse_args()

    main( args.report_path, args.y_axis )
