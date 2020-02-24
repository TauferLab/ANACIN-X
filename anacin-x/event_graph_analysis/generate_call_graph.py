#!/usr/bin/env python3

import argparse
import pickle as pkl
import pprint

# For analyzing ELF files and DWARF debugging information
from elftools.common.py3compat import maxint, bytes2str
from elftools.dwarf.descriptions import describe_form_class
from elftools.elf.elffile import ELFFile

from callstack_analysis import validate, decode_address, lookup_location

def get_addresses( kdts ):
    all_addresses = set()
    for slice_idx,data in kdts.items():
        for run_idx,callstack_data in data["callstack"].items():
            for callstack in callstack_data:
                addresses = [ x.strip() for x in callstack.split(",") ]
                for a in addresses:
                    all_addresses.add( a )
    return all_addresses

def translate_addresses( addresses, executable_path ):
    with open( executable_path, "rb" ) as infile:
        elf_file = ELFFile( infile )
        validate( elf_file )
        translated = {}
        dwarf_info = elf_file.get_dwarf_info()
        for a in addresses:
            fn = decode_address( dwarf_info, a )
            if fn is not None:
                containing_file, line_num = lookup_location( dwarf_info, a )
                containing_file = str( containing_file, encoding="ascii" )
                fn_name = str( fn, encoding="ascii" )
                translated[ a ] = { "name" : fn_name,
                                    "file" : containing_file,
                                    "line" : line_num }
        return translated


def main( kdts_path, executable_path ):
    with open( kdts_path, "rb" ) as infile:
        kdts = pkl.load( infile )

    addresses = get_addresses( kdts )

    
    translated = translate_addresses( addresses, executable_path )
    pprint.pprint( translated )


if __name__ == "__main__":
    desc="Generates the function call-graph for an MPI application"
    parser = argparse.ArgumentParser(description=desc)
    parser.add_argument("kdts_path", 
                        help="Path to pickle file mapping slice indices to callstack data")
    parser.add_argument("executable_path",
                        help="Path to executable that was traced to generate all trace data")
    args = parser.parse_args()

    main( args.kdts_path, args.executable_path )
