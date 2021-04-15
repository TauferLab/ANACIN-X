#!/usr/bin/env bash


# User Input
#comm_pattern=$1
run_count=$1
results_path=$2


# Comm Pattern definition
comm_pattern="message_race"
#comm_pattern="amg2013"
#comm_pattern="unstructured_mesh"

# Pick a scheduler
scheduler=lsf
#scheduler=slurm
#scheduler=unscheduled

# Define Needed Paths
source ./apps/comm_pattern_generator/${scheduler}/example_paths_${scheduler}.config
cd apps/comm_pattern_generator/${scheduler}
example_paths_dir=$(pwd)
cd -
#root_path=$HOME/Src_ANACIN-X
#anacin_x_root=$HOME/Src_ANACIN-X
config_path=${anacin_x_root}/apps/comm_pattern_generator/config
comm_pattern_path=${anacin_x_root}/apps/comm_pattern_generator/${scheduler}
#results_path=/data/gclab/anacin-n/anacin_results/${comm_pattern}



# Decide the Message Sizes to use
message_sizes=(512)

# Decide number of iterations
num_iters=(1)

# Decide number of processes
num_procs=(16)

#Other variables needed
#nd_neighbor_fraction=0.2
n_nodes=1

if [ ${scheduler} == "slurm" ]; then
    slurm_queue="normal"
    slurm_time_limit=5
fi

# Run Comm Pattern Script
for n_iters in ${num_iters[@]};
do
    for n_procs in ${num_procs[@]};
    do
	for msg_sizes in ${message_sizes[@]};
	do
	    if [ ${comm_pattern} == "message_race" ]; then
		bash ${comm_pattern_path}/${comm_pattern}_${scheduler}.sh ${n_procs} ${n_iters} ${msg_sizes} ${n_nodes} ${slurm_queue} ${slurm_time_limit} 0 $((run_count-1)) ${results_path} ${example_paths_dir}
	    elif [ ${comm_pattern} == "amg2013" ]; then
		bash ${comm_pattern_path}/${comm_pattern}_${scheduler}.sh ${n_procs} ${n_iters} ${msg_sizes} ${n_nodes} ${slurm_queue} ${slurm_time_limit} 0 $((run_count-1)) ${results_path} ${example_paths_dir}
	    elif [ ${comm_pattern} == "unstructured_mesh" ]; then
		bash ${comm_pattern_path}/${comm_pattern}_${scheduler}.sh ${n_procs} ${n_iters} ${msg_sizes} ${n_nodes} ${slurm_queue} ${slurm_time_limit} 0 $((run_count-1)) ${results_path} ${example_paths_dir}
	    fi
	done
    done
done
