#!/usr/bin/env bash

#SBATCH -o compute_kdts-%j.out
#SBATCH -e compute_kdts-%j.err

n_procs=$1
compute_kdts_script=$2
traces_dir=$3
graph_kernel=$4

# Determine number of nodes we need to run on
system=$(hostname | sed 's/[0-9]*//g')
if [ ${system} == "quartz" ]; then
    n_procs_per_node=36
elif [ ${system} == "catalyst" ]; then
    n_procs_per_node=24
fi
n_nodes=$(echo "(${n_procs} + ${n_procs_per_node} - 1)/${n_procs_per_node}" | bc)

srun -N${n_nodes} -n${n_procs} ${compute_kdts_script} ${traces_dir} ${graph_kernel} --callstacks_available --slice_dir_name "slices" -o "kdts.pkl"
