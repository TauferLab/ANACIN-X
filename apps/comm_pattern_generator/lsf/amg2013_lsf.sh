#!/usr/bin/env bash                                                                                                                         

n_procs=$1
run_idx_low=$2
run_idx_high=$3
results_root=$4

source ./example_paths_lsf.config

amg2013_script=${anacin_x_root}/apps/comm_pattern_generator/lsf/amg2013.sh

bsub ${amg2013} ${n_procs} ${run_idx_low} ${run_idx_high} ${results_root}
