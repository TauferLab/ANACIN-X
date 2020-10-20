#!/usr/bin/env bash                                                                                                                         

n_procs=$1
run_idx_low=$2
run_idx_high=$3
results_root=$4

source ./example_paths_lsf.config

message_race_script=${anacin_x_root}/apps/comm_pattern_generator/lsf/message_race.sh

bsub ${message_race_script} ${n_procs} ${run_idx_low} ${run_idx_high} ${results_root}
