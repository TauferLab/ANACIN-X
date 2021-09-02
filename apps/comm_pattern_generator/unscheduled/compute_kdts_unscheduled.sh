#!/usr/bin/env bash                                                                                                                                                                                                                           

#BSUB -o compute_kdts-%j.out                                                                                                                                                                                                                  
#BSUB -e compute_kdts-%j.err                                                                                                                                                                                                                  

n_procs=$1
compute_kdts_script=$2
traces_dir=$3
graph_kernel=$4
slicing_policy=$5

echo $@

# Determine number of nodes we need to run on                                                                                                                                                                                                 
#system=$(hostname | sed 's/[0-9]*//g')
#if [ ${system} == "quartz" ]; then
#    n_procs_per_node=36
#elif [ ${system} == "catalyst" ]; then
#    n_procs_per_node=24
#fi
#n_procs_per_node=32
#n_nodes=$(echo "(${n_procs} + ${n_procs_per_node} - 1)/${n_procs_per_node}" | bc)

mpirun -np ${n_procs} ${compute_kdts_script} ${traces_dir} ${graph_kernel} --slicing_policy ${slicing_policy} -o "kdts.pkl" -c
