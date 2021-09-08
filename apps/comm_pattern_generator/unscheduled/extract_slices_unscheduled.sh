#!/usr/bin/env bash                                                                                                                                                                                                                           

n_procs=$1
extract_slices_script=$2
event_graph=$3
slicing_policy=$4

# Determine number of nodes we need to run on                                                                                                                                                                                                 
#system=$(hostname | sed 's/[0-9]*//g')
#if [ ${system} == "quartz" ]; then
#    n_procs_per_node=36
#elif [ ${system} == "catalyst" ]; then
#    n_procs_per_node=24
#fi
#n_nodes=$(echo "(${n_procs} + ${n_procs_per_node} - 1)/${n_procs_per_node}" | bc)

mpirun -np ${n_procs} ${extract_slices_script} ${event_graph} ${slicing_policy} -o "slices"
