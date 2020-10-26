#!/usr/bin/env bash                                                                                                                         

n_procs=$1
n_iters=$2
run_idx_low=$3
run_idx_high=$4
results_root=$5
msg_sizes=$6

source ./example_paths_lsf.config

message_race_script=${anacin_x_root}/apps/comm_pattern_generator/lsf/message_race.sh

bsub > ${debugging_path}/lsf_output.txt 2> ${debugging_path}/lsf_error.txt ${message_race_script} ${n_procs} ${n_iters} ${run_idx_low} ${run_idx_high} ${results_root} ${msg_sizes}
