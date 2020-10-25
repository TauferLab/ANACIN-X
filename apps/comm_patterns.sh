#!/usr/bin/env bash


# To Make this Script Work
# 1. Turn msg_sizes into a pass
# 2. Make mini mcb and unstructured mesh take n_procs as pass
# 3. Have generators use n_nodes dynamically


# User Input
n_procs=$1
n_nodes=$2
comm_pattern=$3
scheduler=$4
run_idx_low=$5
run_idx_high=$6


# Define Needed Paths
root_path=$HOME/Src_ANACIN-X
config_path=${root_path}/apps/comm_pattern_generator/config
comm_pattern_path=${root_path}/apps/comm_pattern_generator/${scheduler}
results_path=/data/gclab/anacin-n/anacin_results/${comm_pattern}


# Reset results path
#cd ${results_path}
#rm -r ./*
#cd root_path/apps


# Pick a scheduler
#scheduler=lsf
#scheduler=slurm


# Decide the Message Sizes and Number of Iterations to Use
# (Currently doesn't work with msg_size=1
msg_sizes=(512 2048)
n_iters=10
nd_neighbor_fraction=0.2


# Run Comm Pattern Script
if [ ${comm_pattern} == "message_race" ]; then
    sh ${comm_pattern_path}/${comm_pattern}_${scheduler}.sh ${n_procs} ${n_iters} ${run_idx_low} ${run_idx_high} ${results_path} ${msg_sizes}
elif [ ${comm_pattern} == "amg2013" ]; then
    sh ${comm_pattern_path}/${comm_pattern}_${scheduler}.sh ${n_procs} ${n_iters} ${run_idx_low} ${run_idx_high} ${results_path} ${msg_sizes}
elif [ ${comm_pattern} == "mini_mcb" ]; then
    sh ${comm_pattern_path}/${comm_pattern}_${scheduler}.sh ${run_idx_low} ${run_idx_high} ${n_nodes} ${results_path}
elif [ ${comm_pattern} == "unstructured_mesh" ]; then
    sh ${comm_pattern_path}/${comm_pattern}_${scheduler}.sh ${run_idx_low} ${run_idx_high} ${n_nodes} ${results_path}
fi
