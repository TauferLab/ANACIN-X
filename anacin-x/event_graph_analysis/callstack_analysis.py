#!/usr/bin/env python3

import glob
import os
import argparse
import pickle
import json

import pprint

# For analyzing ELF files and DWARF debugging information
from elftools.common.py3compat import maxint, bytes2str
from elftools.dwarf.descriptions import describe_form_class
from elftools.elf.elffile import ELFFile

# For constructing call tree from set of callstacks
import igraph

from utilities import timer, read_graphs_parallel, read_graphs_serial, merge_dicts



# Check that input contains sufficient information to proceed:
# 1. Executable has DWARF info
def validate( elf_file ):
    # Check DWARF info is present
    if not elf_file.has_dwarf_info():
        raise RuntimeError("Executable does not have DWARF info")

def get_all_trace_dirs( traces_root_dir ):
    all_trace_dirs = glob.glob( traces_root_dir + "/run*/" )
    all_trace_dirs = sorted( all_trace_dirs, key=lambda x: int(x.split("/")[-2][3:]) )
    return all_trace_dirs

def get_slice_dirs( trace_dirs, slicing_policy ):
    trace_dir_to_slice_dir = {}
    for td in trace_dirs:
        slice_dir = td + "/slices_"
        for idx,kvp in enumerate(slicing_policy.items()):
            key,val = kvp
            slice_dir += str(key) + "_" + str(val)
            if idx < len(slicing_policy)-1:
                slice_dir += "_"
        slice_dir += "/"
        trace_dir_to_slice_dir[ td ] = slice_dir
    return trace_dir_to_slice_dir


# From https://github.com/eliben/pyelftools/blob/master/examples/dwarf_decode_address.py
def decode_address( dwarf_info, address ):
    address = int(address, 0)
    for CU in dwarf_info.iter_CUs():
        for DIE in CU.iter_DIEs():
            try:
                if DIE.tag == "DW_TAG_subprogram":
                    low_pc = DIE.attributes["DW_AT_low_pc"].value
                    high_pc_attr = DIE.attributes["DW_AT_high_pc"]
                    high_pc_attr_class = describe_form_class( high_pc_attr.form )
                    if high_pc_attr_class == "address":
                        high_pc = high_pc_attr.value
                    elif high_pc_attr_class == "constant":
                        high_pc = low_pc + high_pc_attr.value
                    else:
                        print('Error: invalid DW_AT_high_pc class:',
                              high_pc_attr_class)
                        continue
                    if low_pc <= address <= high_pc:
                        return DIE.attributes['DW_AT_name'].value
            except KeyError:
                continue
    return None

# From https://github.com/eliben/pyelftools/blob/master/examples/dwarf_decode_address.py
def lookup_location( dwarf_info, address ):
    address = int(address, 0)
    for CU in dwarf_info.iter_CUs():
        # First, look at line programs to find the file/line for the address
        lineprog = dwarf_info.line_program_for_CU(CU)
        prevstate = None
        for entry in lineprog.get_entries():
            # We're interested in those entries where a new state is assigned
            if entry.state is None:
                continue
            if entry.state.end_sequence:
                # if the line number sequence ends, clear prevstate.
                prevstate = None
                continue
            # Looking for a range of addresses in two consecutive states that
            # contain the required address.
            if prevstate and prevstate.address <= address < entry.state.address:
                filename = lineprog['file_entry'][prevstate.file - 1].name
                line = prevstate.line
                return filename, line
            prevstate = entry.state
    return None, None



def get_callstacks( slice_indices, slice_idx_to_data ):
    # Filter down to callstack data only
    slice_idx_to_callstacks = { k:v["callstack"] for k,v in slice_idx_to_data.items() }
    callstack_to_total = {}
    for slice_idx in slice_indices:
        run_idx_to_callstacks = slice_idx_to_callstacks[ slice_idx ]
        for run_idx,callstack_to_count in run_idx_to_callstacks.items():
            for cs,count in callstack_to_count.items():
                if cs not in callstack_to_total:
                    callstack_to_total[ cs ] = count
                else:
                    callstack_to_total[ cs ] += count
    return callstack_to_total



#def main( flagged_slices_path, traces_root_dir, slicing_policy_path, executable_path ):    
def main( flagged_slices_path, kdts_path, executable_path ):    

    # Ingest mapping from anomaly-detection policies to lists of flagged slices
    with open( flagged_slices_path, "rb" ) as infile:
        policy_to_flagged_indices = pickle.load( infile )

    #pprint.pprint( policy_to_flagged_indices )

    # Ingest mapping from slice indices to callstack data
    with open( kdts_path, "rb" ) as infile:
        slice_idx_to_data = pickle.load( infile )
        #slice_idx_to_callstacks = { k:v["callstack"] for k,v in kdts.items() }

    # Validate executable we'll be querying later
    with open( executable_path, "rb" ) as executable_infile:
        elf_file = ELFFile( executable_infile )
        validate( elf_file )

    ## Read in slicing policy
    ## This will tell us which sub-directory of the trace directory to look in
    ## for the slice subgraph 
    #with open( slicing_policy_path, "r" ) as infile:
    #    slicing_policy = json.load( infile )

    ## Determine set of slices to compute over based on slicing policy
    #trace_dirs = get_all_trace_dirs( traces_root_dir )
    #trace_dir_to_slice_dir = get_slice_dirs( trace_dirs, slicing_policy )

    ## Sort slice dirs in run order 
    ##slice_dirs = sorted( trace_dir_to_slice_dir.values(), key=lambda x:  int(os.path.abspath(x).split("/")[-2][3:]) )
    #slice_dirs = sorted( [ td + "/slices_mesh_refinement_events/" for td in trace_dirs ], key=lambda x: int(os.path.abspath(x).split("/")[-2][3:]) )

    # For each anomaly detection policy, load in the slice subgraphs 
    # corresponding to the flagged slice indices
    for policy,slice_indices in policy_to_flagged_indices.items():
        
        callstack_to_count = get_callstacks( slice_indices, slice_idx_to_data )
                    
        #callstack_to_count = {}
        #for slice_idx in slice_indices:
        #    print("Policy: {} - Loading slice subgraphs for slice index: {}".format( policy, slice_idx ))
        #    # Load slice subgraphs for this index
        #    slice_paths = [ sd + "/slice_" + str(slice_idx) + ".graphml" for sd in slice_dirs ]
        #    slice_subgraphs = read_graphs_parallel( slice_paths ) ### getting OSError too many open files?
        #    #slice_subgraphs = read_graphs_serial( slice_paths )
        #    #slice_subgraphs = [] 
        #    #for sd in slice_dirs:
        #    #    slice_subgraph_path = sd + "/slice_" + str(slice_idx) + ".graphml"
        #    #    slice_subgraph = read_graph( slice_subgraph_path )
        #    #    slice_subgraphs.append( slice_subgraph )

        #    # Extract call-stack information from the slice subgraphs
        #    #callstack_to_count = {}
        #    for g in slice_subgraphs:
        #        callstacks = g.vs[:]["callstack"]
        #        # Filter out empties
        #        callstacks = list( filter( lambda cs: cs != "", callstacks ) )
        #        # Aggregate into map from unique callstacks to # times appearing
        #        for cs in callstacks:
        #            if cs not in callstack_to_count:
        #                callstack_to_count[ cs ] = 1
        #            else:
        #                callstack_to_count[ cs ] += 1


        # Clean up callstacks
        cleaned_callstack_to_count = {}
        for cs,count in callstack_to_count.items():
            frames = [ frame.strip() for frame in cs.strip().split(",") ]
            cleaned_callstack_to_count[ tuple(frames) ] = count


        print("Collected callstack counts. Starting callstack translation...") 
        address_to_translation = {}
        translated_callstack_to_count = {}
        fn_to_location = {}
        with open( executable_path, "rb" ) as executable_infile:
            # Load in the executable
            elf_file = ELFFile( executable_infile )
            # Get its debug info
            dwarf_info = elf_file.get_dwarf_info()
            ## Translate frames
            #address_to_translation = {}
            #translated_callstack_to_count = {}
            ## Get locations
            #fn_to_location = {}
            for callstack,count in cleaned_callstack_to_count.items():
                translated_callstack = []
                for address in callstack:
                    # If we haven't translated this address before, do so
                    if address not in address_to_translation:
                        func_name = decode_address( dwarf_info, address )
                        containing_file, line_num = lookup_location( dwarf_info, address )
                        if func_name is not None:
                            func_name = str( func_name, encoding="ascii" )
                            if func_name not in fn_to_location:
                                containing_file = str( containing_file, encoding="ascii" )
                                fn_to_location[ func_name ] = { "file" : containing_file, 
                                                                "line" : line_num }
                        address_to_translation[ address ] = func_name
                    # If we have, just look it up
                    else:
                        func_name = address_to_translation[ address ]
                    # Append the newly translated callstack
                    translated_callstack.append( func_name )

                # Filter out any parts of the callstack that were not translated, 
                translated_callstack = filter( lambda x: x is not None, translated_callstack ) 
                # Convert back to strings
                # Make tuple so key-able
                translated_callstack = tuple( translated_callstack )
                translated_callstack_to_count[ translated_callstack ] = count
        print("Done with callstack translation. Creating report...")


        traces_dir = os.path.dirname( kdts_path )
        report_file = traces_dir + "/anomaly_report_for_policy_" + policy + ".txt"
        with open( report_file, "w" ) as outfile:
            ### Print out report of potential root causes of non-determinism
            outfile.write("Report for anomaly detection policy: {}\n".format( policy ))
            outfile.write("-----------------------------------------------------------\n")
            outfile.write("Call-stack to # occurrences:\n")
            for callstack,count in translated_callstack_to_count.items():
                callstack_str = ""
                for idx,call in enumerate(reversed(callstack)):
                    callstack_str += call 
                    if idx != len(callstack)-1:
                        callstack_str += " --> "
                outfile.write("{} : {}\n".format(callstack_str, count))
            outfile.write("-----------------------------------------------------------\n")
            outfile.write("Locations of functions occurring in identified call-stacks:\n")
            for fn,loc in fn_to_location.items():
                outfile.write("Function: {}, File: {}, Line Number: {}\n".format(fn,loc["file"],loc["line"]))
            outfile.write("-----------------------------------------------------------\n")






if __name__ == "__main__":
    desc=""
    parser = argparse.ArgumentParser(description=desc)
    parser.add_argument("flagged_slices_path", 
                        help="Path to pickle file mapping anomaly detection policies to sets of anomalous slices")
    parser.add_argument("kdts_path", 
                        help="Path to pickle file mapping slice indices to callstack data")
    #parser.add_argument("traces_root_dir", default=None,
    #                    help="The top-level directory containing all trace data")
    #parser.add_argument("slicing_policy",
    #                    help="Path to a JSON file describing how to slice the event graph")
    parser.add_argument("executable",
                        help="Path to executable that was traced to generate all trace data")
    args = parser.parse_args()

    main( args.flagged_slices_path, args.kdts_path, args.executable )
    #main( args.flagged_slices_path, args.traces_root_dir, args.slicing_policy, args.executable )
