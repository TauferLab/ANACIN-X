#!/usr/bin/env bash

n_procs=$1
comm_pattern=$2

root_path=$HOME/Src_ANACIN-X
results_path=/data/gclab/anacin-n/anacin_results/${comm_pattern}

# Reset results path
#cd ${results_path}
#rm -r ./*
#cd root_path/apps

# Pick a scheduler
scheduler=lsf
scheduler=slurm

# Decide the Message Sizes to Use
# (Currently doesn't work with msg_size=1
msg_sizes=(512 2048)
