#!/usr/bin/env bash


# To Make this Script Work
# 1. Turn msg_sizes into a pass
# 2. Make mini mcb and unstructured mesh take n_procs as pass
# 3. Have generators use n_nodes dynamically


# User Input
#n_procs=$1
comm_pattern=$1
#scheduler=$2
#n_nodes=$2
#run_idx_low=$2
#run_idx_high=$3
run_count$2
results_path=$3

# Define Needed Paths
root_path=$HOME/Src_ANACIN-X
config_path=${root_path}/apps/comm_pattern_generator/config
comm_pattern_path=${root_path}/apps/comm_pattern_generator/${scheduler}
#results_path=/data/gclab/anacin-n/anacin_results/${comm_pattern}


# Reset results path
#cd ${results_path}
#rm -r ./*
#cd root_path/apps


# Pick a scheduler
scheduler=lsf
#scheduler=slurm


# Decide the Message Sizes to use
# (Currently doesn't work with msg_size=1 unless on message race
msg_sizes=(512 2048)

# Decide number of iterations
n_iters=(1)

# Decide number of processes
n_procs=(10)

#Other variables needed
nd_neighbor_fraction=0.2
n_nodes=1


# Run Comm Pattern Script
if [ ${comm_pattern} == "message_race" ]; then
    sh ${comm_pattern_path}/${comm_pattern}_${scheduler}.sh ${n_procs} ${n_iters} 1 ${run_count} ${results_path} ${msg_sizes}
elif [ ${comm_pattern} == "amg2013" ]; then
    sh ${comm_pattern_path}/${comm_pattern}_${scheduler}.sh ${n_procs} ${n_iters} 1 ${runc_count} ${results_path} ${msg_sizes}
elif [ ${comm_pattern} == "mini_mcb" ]; then
    sh ${comm_pattern_path}/${comm_pattern}_${scheduler}.sh 1 ${run_count} ${n_nodes} ${n_iters} ${results_path} ${n_procs}
elif [ ${comm_pattern} == "unstructured_mesh" ]; then
    sh ${comm_pattern_path}/${comm_pattern}_${scheduler}.sh 1 ${run_count} ${n_nodes} ${n_iters} ${results_path} ${n_procs} ${msg_sizes}
fi
