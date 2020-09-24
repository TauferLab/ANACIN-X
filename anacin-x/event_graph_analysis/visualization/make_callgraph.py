#!/usr/bin/env python3
import sys
sys.path.append("../")
sys.path.append("./")

import argparse
import igraph
import re
import pprint
import pickle as pkl
import matplotlib
matplotlib.use('TkAgg')
import matplotlib.pyplot as plt

from elftools.elf.elffile import ELFFile

from callstack_analysis import ( get_callstack_to_count, 
                                 translate_callstacks, 
                                 validate_executable,
                                 get_call_set,
                                 get_caller_callee_pairs
                               )




def normalize_counts( pair_to_count ):
    max_count = max(pair_to_count.values())
    return { pair:count/max_count for pair,count in pair_to_count.items() }

def main( kdts_data_path, executable_path, flagged_slices_path, flagging_policy ):
    with open( kdts_data_path, "rb" ) as kdts_infile:
        kdts = pkl.load( kdts_infile )
        slice_to_callstacks = { k:v["callstack"] for k,v in kdts.items() }

    with open( executable_path, "rb" ) as executable_infile:
        elf_file = ELFFile( executable_infile )
        validate_executable( elf_file )
    
    with open( flagged_slices_path, "rb" ) as infile:
        policy_to_flagged_indices = pkl.load( infile )
        if len( policy_to_flagged_indices ) == 1:
            policy = list(policy_to_flagged_indices.keys())[0]
            flagged_slice_indices = policy_to_flagged_indices[policy]
        else:
            if flagging_policy is not None:
                flagged_slice_indices = policy_to_flagged_indices[flagging_policy]
            else:
                policies = policy_to_flagged_indices.keys()
                raise RuntimeError("Multiple flagging policies provided but none selected. Pick one of: {}".format(polices))
    
    # Unpack data
    #slice_indices = sorted(slice_to_callstacks.keys())
    slice_indices = [0, 5]
    flagged_slice_indices = [5]

    callstack_to_count = get_callstack_to_count( slice_indices, slice_to_callstacks )
    translated_callstack_to_count, address_to_translation = translate_callstacks( callstack_to_count, executable_path )
    call_set = get_call_set( translated_callstack_to_count )
    pair_to_count = get_caller_callee_pairs( translated_callstack_to_count )
    pair_to_freq = normalize_counts( pair_to_count )
    #pprint.pprint(translated_callstack_to_count)
    #pprint.pprint(pair_to_count)

    # Unpack flagged data
    flagged_callstack_to_count = get_callstack_to_count( flagged_slice_indices, slice_to_callstacks )
    translated_flagged_callstack_to_count, address_to_translation = translate_callstacks( callstack_to_count, executable_path, address_to_translation )
    flagged_call_set = get_call_set( translated_flagged_callstack_to_count )
    flagged_pair_to_count = get_caller_callee_pairs( translated_flagged_callstack_to_count )
    
    # Set up to build callgraph
    vid_to_call = { vid:call for vid,call in zip(range(len(call_set)),sorted(call_set)) }
    call_to_vid = { call:vid for vid,call in vid_to_call.items() }
    eid_to_pair = { eid:pair for eid,pair in zip(range(len(pair_to_count.keys())), sorted(pair_to_count.keys())) }
    #pprint.pprint( vid_to_call )
    #pprint.pprint( eid_to_pair )

    # Build callgraph 
    callgraph = igraph.Graph(directed=True)
    callgraph.add_vertices( len(vid_to_call.keys()) )
    for i in range(len(callgraph.vs[:])):
        v = callgraph.vs[i]
        v["function"] = vid_to_call[i]
        if vid_to_call[i] in flagged_call_set:
            v["color"] = "lightcoral"
        else:
            v["color"] = "lightgrey"
    edges = []
    edge_weights = []
    edge_colors = []
    for _,pair in eid_to_pair.items():
        caller, callee = pair
        caller_vid = call_to_vid[caller]
        callee_vid = call_to_vid[callee]
        edges.append( [ caller_vid, callee_vid ] )
        edge_weights.append( pair_to_freq[ pair ] )
        if pair in flagged_pair_to_count:
            edge_colors.append( "red" )
        else:
            edge_colors.append( "dimgrey" )
    callgraph.add_edges( edges )
    callgraph.es[:]["frequency"] = edge_weights
    callgraph.es[:]["color"] = edge_colors
    #for v in callgraph.vs[:]:
    #    print(v)
    #for e in callgraph.es[:]:
    #    print("Edge: {} --> {}, weight = {}".format(e.source, e.target, e["weight"]))
    
    # Configure plot appearance
    layout = callgraph.layout_sugiyama()
    n_vertices = len(callgraph.vs[:])
    vertex_label_distances = [ 2 ] * n_vertices
    edge_width_scale = 2
    edge_widths = [ ew*edge_width_scale for ew in callgraph.es[:]["frequency"] ]
    save_path = "callgraph.png"


    # Make plot
    igraph.plot( callgraph,
                 bbox=(2000, 1000),
                 layout = layout,
                 vertex_color = callgraph.vs[:]["color"],
                 vertex_label = callgraph.vs[:]["function"],
                 vertex_label_dist = vertex_label_distances,
                 edge_width = edge_widths,
                 edge_color = callgraph.es[:]["color"],
                 margin=80,
                 target = save_path )


if __name__ == "__main__":
    desc = ""
    parser = argparse.ArgumentParser(description=desc)
    parser.add_argument("kdts_data",
                        help="Pickle file containing callstack data for each slice")
    parser.add_argument("executable",
                        help="Executable for address translation")
    parser.add_argument("flagged_slices",
                        help="Pickle file containing flagged slice indices")
    parser.add_argument("-f", "--flagging_policy", required=False, default=None,
                        help="If more than one anomaly detection policy is stored in flagged slices, pick one with this flag")
    args = parser.parse_args()

    main( args.kdts_data, args.executable, args.flagged_slices, args.flagging_policy )
