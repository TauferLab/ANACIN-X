#!/usr/bin/env bash                                                                                                                         

n_procs=$1
n_iters=$2
msg_size=$3
n_nodes=$4
run_idx_low=$5
run_idx_high=$6
results_root=$7

source ./example_paths_lsf.config

message_race_script=${anacin_x_root}/apps/comm_pattern_generator/lsf/message_race.sh

n_procs_per_node=$((n_procs/n_nodes))

#bsub -n ${n_procs} ${message_race_script} ${n_procs} ${n_iters} ${msg_size} ${run_idx_low} ${run_idx_high} ${results_root}
bsub -n ${n_procs} -R "span[ptile=${n_procs_per_node}]" -o ${debugging_path}/lsf_output.txt -e ${debugging_path}/lsf_error.txt ${message_race_script} ${n_procs} ${n_iters} ${msg_size} ${n_nodes} ${run_idx_low} ${run_idx_high} ${results_root}
