#!/usr/bin/env bash                                                                                                                         

n_procs=$1
n_iters=$2
run_idx_low=$3
run_idx_high=$4
results_root=$5
msg_sizes=$6

source ./example_paths_lsf.config

amg2013_script=${anacin_x_root}/apps/comm_pattern_generator/lsf/amg2013.sh

bsub -o ${debugging_path}/lsf_output.txt -e ${debugging_path}/lsf_error.txt ${amg2013_script} ${n_procs} ${run_idx_low} ${run_idx_high} ${results_root} ${msg_sizes}
