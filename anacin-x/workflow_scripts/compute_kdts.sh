#!/usr/bin/env bash                                                                                                                                                                                                                           


n_procs=$1
compute_kdts_script=$2
traces_dir=$3
graph_kernel=$4
slicing_policy=$5
paths_dir=$6


source ${paths_dir}/anacin_paths.config

if [ "${run_csmpi}" == "True" ]; then
	mpirun -np ${n_procs} ${compute_kdts_script} ${traces_dir} ${graph_kernel} --slicing_policy ${slicing_policy} -o "kdts.pkl" --slice_dir_name "slices" -c
else
	mpirun -np ${n_procs} ${compute_kdts_script} ${traces_dir} ${graph_kernel} --slicing_policy ${slicing_policy} -o "kdts.pkl" --slice_dir_name "slices"
fi
