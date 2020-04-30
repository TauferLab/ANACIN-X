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
def validate_executable( elf_file ):
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



def get_callstack_to_count( slice_indices, slice_idx_to_callstacks ):
    callstack_to_total = {}
    for slice_idx in slice_indices:
        run_idx_to_callstacks = slice_idx_to_callstacks[ slice_idx ]
        for run_idx,callstack_to_count in run_idx_to_callstacks.items():
            for cs,count in callstack_to_count.items():
                if cs not in callstack_to_total:
                    callstack_to_total[ cs ] = count
                else:
                    callstack_to_total[ cs ] += count
    return clean_callstacks(callstack_to_total)

def clean_callstacks( callstack_to_count ):
    cleaned_callstack_to_count = {}
    for cs,count in callstack_to_count.items():
        frames = [ frame.strip() for frame in cs[0].strip().split(",") ]
        frames.append( cs[-1] )
        cleaned_callstack_to_count[ tuple(frames) ] = count
    return cleaned_callstack_to_count
        

def get_call_set( translated_callstack_to_count ):
    unique_calls = set()
    for callstack in translated_callstack_to_count:
        for call in callstack:
            unique_calls.add( call )
    return unique_calls


def get_caller_callee_pairs( translated_callstack_to_count ):
    pair_to_count = {}
    for callstack,count in translated_callstack_to_count.items():
        for i in range(1, len(callstack)):
            caller = callstack[i-1]
            callee = callstack[i]
            pair = ( caller, callee )
            if pair not in pair_to_count:
                pair_to_count[ pair ] = count
            else:
                pair_to_count[ pair ] += count
    return pair_to_count

def translate_callstacks( callstack_to_count, executable_path, address_to_translation=None ):
    translated_callstack_to_count = {}
    with open( executable_path, "rb" ) as executable_infile:
        # Load in the executable
        elf_file = ELFFile( executable_infile )
        # Get its debug info
        dwarf_info = elf_file.get_dwarf_info()
        ## Translate 
        if address_to_translation is None:
            address_to_translation = {}
        for callstack,count in callstack_to_count.items():
            translated_callstack = []
            for address in callstack[:-1]:
                # If we haven't translated this address before, do so
                if address not in address_to_translation:
                    func_name = decode_address( dwarf_info, address )
                    if func_name is not None:
                        func_name = str( func_name, encoding="ascii" )
                        address_to_translation[ address ] = func_name
                # If we have, just look it up
                else:
                    func_name = address_to_translation[ address ]
                # Append the newly translated callstack
                translated_callstack.append( func_name )

            # Filter out any parts of the callstack that were not translated, 
            translated_callstack = list( filter( lambda x: x is not None, translated_callstack ) )
            # Tack MPI function back on
            translated_callstack = [ callstack[-1] ] + translated_callstack
            # Convert back to strings
            # Make tuple so key-able
            translated_callstack = tuple( reversed(translated_callstack) )
            translated_callstack_to_count[ translated_callstack ] = count
    return translated_callstack_to_count, address_to_translation
    

#def main( flagged_slices_path, traces_root_dir, slicing_policy_path, executable_path ):    
def main( flagged_slices_path, kdts_path, executable_path ):    

    # Ingest mapping from anomaly-detection policies to lists of flagged slices
    with open( flagged_slices_path, "rb" ) as infile:
        policy_to_flagged_indices = pickle.load( infile )

    #pprint.pprint( policy_to_flagged_indices )

    # Ingest mapping from slice indices to callstack data
    with open( kdts_path, "rb" ) as infile:
        slice_idx_to_data = pickle.load( infile )
        slice_idx_to_callstacks = { k:v["callstack"] for k,v in slice_idx_to_data.items() }

    # Validate executable we'll be querying later
    with open( executable_path, "rb" ) as executable_infile:
        elf_file = ELFFile( executable_infile )
        validate_executable( elf_file )
    
    # For each anomaly detection policy, load in the slice subgraphs 
    # corresponding to the flagged slice indices
    for policy,slice_indices in policy_to_flagged_indices.items():
       
        all_slice_indices = set( slice_idx_to_data.keys() )
        non_flagged_indices = all_slice_indices - set(slice_indices)

        #callstack_to_count = get_callstack_to_count( slice_indices, slice_idx_to_callstacks )
        callstack_to_count = get_callstack_to_count( non_flagged_indices, slice_idx_to_callstacks )
                    
        ## Clean up callstacks
        #cleaned_callstack_to_count = {}
        #for cs,count in callstack_to_count.items():
        #    frames = [ frame.strip() for frame in cs[0].strip().split(",") ]
        #    frames.append( cs[-1] )
        #    cleaned_callstack_to_count[ tuple(frames) ] = count
                

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
            for callstack,count in callstack_to_count.items():
                translated_callstack = []
                for address in callstack[:-1]:
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
                translated_callstack = list( filter( lambda x: x is not None, translated_callstack ) )
                # Tack MPI function back on
                translated_callstack = [ callstack[-1] ] + translated_callstack
                # Convert back to strings
                # Make tuple so key-able
                translated_callstack = tuple( translated_callstack )
                translated_callstack_to_count[ translated_callstack ] = count
        print("Done with callstack translation. Creating report...")


        traces_dir = os.path.dirname( kdts_path )
        report_file = traces_dir + "/non_anomaly_report_for_policy_" + policy + ".txt"
        #report_file = traces_dir + "/anomaly_report_for_policy_" + policy + ".txt"
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
