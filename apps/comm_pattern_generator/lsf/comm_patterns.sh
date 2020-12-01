#!/usr/bin/env bash


# To Make this Script Work
# /1. Turn msg_sizes into a pass
# /2. Make mini mcb and unstructured mesh take n_procs as pass
# 3. Have generators use n_nodes dynamically


# User Input
#n_procs=$1
comm_pattern=$1
#scheduler=$2
#n_nodes=$2
#run_idx_low=$2
#run_idx_high=$3
run_count=$2
results_path=$3


# Pick a scheduler
scheduler=lsf
#scheduler=slurm

# Define Needed Paths
root_path=$HOME/Src_ANACIN-X
config_path=${root_path}/apps/comm_pattern_generator/config
comm_pattern_path=${root_path}/apps/comm_pattern_generator/${scheduler}
#results_path=/data/gclab/anacin-n/anacin_results/${comm_pattern}


# Reset results path
#cd ${results_path}
#rm -r ./*
#cd ${comm_pattern_path}


# Decide the Message Sizes to use
# (Currently doesn't work with msg_size=1 unless on message race
message_sizes=(512)
#message_sizes=(2)

# Decide number of iterations
num_iters=(1)
#num_iters=(2 4 8)
#num_iters=(10)

# Decide number of processes
#num_procs=(4 8 16 32)
num_procs=(16)
#num_procs=(10)

#Other variables needed
nd_neighbor_fraction=0.2
n_nodes=1


# Run Comm Pattern Script
for n_iters in ${num_iters[@]};
do
    for n_procs in ${num_procs[@]};
    do
	for msg_sizes in ${message_sizes[@]};
	do
	    #cd ${results_path}
            rm -rf ${results_path}/*
            #cd ${comm_pattern_path}
	    if [ ${comm_pattern} == "message_race" ]; then
		#bash ${comm_pattern_path}/${comm_pattern}.sh ${n_procs} ${n_iters} ${msg_sizes} 1 ${run_count} ${results_path}
		bash ${comm_pattern_path}/${comm_pattern}_${scheduler}.sh ${n_procs} ${n_iters} ${msg_sizes} 1 ${run_count} ${results_path}
#		cp ${results_path}/msg_size_${msg_sizes}/without_ninja/run_${run_idx}/event_graph.graphml ${results_path}/../comm_pattern_graphs/graph_niters_${n_iters}_nprocs_${n_procs}_msg_size_${msg_sizes}_run_${run_idx}.graphml
	    elif [ ${comm_pattern} == "amg2013" ]; then
		bash ${comm_pattern_path}/${comm_pattern}.sh ${n_procs} ${n_iters} ${msg_sizes} 1 ${run_count} ${results_path}
		#bash ${comm_pattern_path}/${comm_pattern}_${scheduler}.sh ${n_procs} ${n_iters} ${msg_sizes} 1 ${run_count} ${results_path}
	    elif [ ${comm_pattern} == "mini_mcb" ]; then
		bash ${comm_pattern_path}/${comm_pattern}_${scheduler}.sh 1 ${run_count} ${n_nodes} ${n_iters} ${n_procs} ${results_path}
	    elif [ ${comm_pattern} == "unstructured_mesh" ]; then
		bash ${comm_pattern_path}/${comm_pattern}_${scheduler}.sh 1 ${run_count} ${n_nodes} ${n_iters} ${n_procs} ${msg_sizes} ${results_path}
	    fi
	done
    done
done
