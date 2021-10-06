#!/usr/bin/env bash


n_procs=$1
extract_slices_script=$2
event_graph=$3
slicing_policy=$4

mpirun -np ${n_procs} ${extract_slices_script} ${event_graph} ${slicing_policy} -o "slices"
