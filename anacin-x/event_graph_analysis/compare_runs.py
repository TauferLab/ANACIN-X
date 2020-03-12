#!/usr/bin/env python3

#SBATCH -t 01:00:00
#SBATCH -o compare_runs-%j.out
#SBATCH -e compare_runs-%j.err

import pprint

import argparse
import igraph
import numpy as np
import pathlib
import os
import json
import glob

import time

from mpi4py import MPI
comm = MPI.COMM_WORLD

def read_graph( graph_path ):
    graph = igraph.read( graph_path )
    return graph

def assign_slices( n_slices ):
    my_rank = comm.Get_rank()
    comm_size = comm.Get_size()
    slices_per_rank = n_slices / comm_size
    my_slices = list( filter( lambda x : x % comm_size == my_rank, range( n_slices ) ) )
    return my_slices

def main( slice_dir_a, slice_dir_b ):
    my_rank = comm.Get_rank()
    slices_a = sorted( glob.glob( slice_dir_a + "/*.graphml" ) )
    slices_b = sorted( glob.glob( slice_dir_b + "/*.graphml" ) )
    assert( len(slices_a) == len(slices_b) )
    my_slices = assign_slices( len( slices_a ) )
    #print("Rank: {} assigned slices: {}".format( my_rank, my_slices ) )
    for idx in my_slices:
        path_a = slice_dir_a + "/slice_" + str(idx) + ".graphml"
        path_b = slice_dir_b + "/slice_" + str(idx) + ".graphml"
        graph_a = read_graph( path_a )
        graph_b = read_graph( path_b )
        is_iso = graph_a.isomorphic( graph_b )
        if not is_iso:
            print("Rank: {} detected non-isomorphic subgraphs at slice: {}".format( my_rank, idx ) )
        

if __name__ == "__main__":
    desc = ""
    parser = argparse.ArgumentParser(description=desc)
    parser.add_argument("slice_dir_a",
                        help="")
    parser.add_argument("slice_dir_b",
                        help="")
    args = parser.parse_args()
   
    my_rank = comm.Get_rank()
    start_time = time.time()
    
    main( args.slice_dir_a, args.slice_dir_b )
    
    end_time = time.time()
    elapsed = end_time - start_time
    if my_rank == 0:
        print("Total elapsed time: {}".format( elapsed ))
