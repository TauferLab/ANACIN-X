#!/usr/bin/env bash


# User Input
#comm_pattern=$1
#run_count=$1
#n_procs=$1
#n_iters=$2
#msg_sizes=$3
#n_nodes=$4
#slurm_queue=$5
#slurm_time_limit=$6
#run_count=$7
#results_path=$1


while [ -n "$1" ]; do
    case "$1" in
	    -p) n_procs=$2;;
	    -i) n_iters=$2;;
	    -s) msg_sizes=$2;;
	    -n) n_nodes=$2;; 
	    -q) slurm_queue=$2;;
	    -t) slurm_time_limit=$2;;
	    -r) run_count=$2;;
	    -o) results_path=$2 ;;
	    *) echo "$1 is not an option" ;;
    esac
    shift
    shift
done

# Comm Pattern definition
while true; do
    read -p "Which communication pattern would you like to analyze? Input is case sensitive. (message_race, amg2013, unstructured_mesh) " comm_pattern
    case ${comm_pattern} in
	    "message_race" | "amg2013" | "unstructured_mesh" ) break ;;
	    * ) echo "Please respond with one of the listed options. Input is case sensitive. (message_race, amg2013, unstructured_mesh) " ;;
    esac
done

# Pick a scheduler
while true; do
    read -p "Which job scheduler would you like to use? Input is case sensitive. (lsf, slurm, unscheduled) " scheduler
    case ${scheduler} in
            "lsf" | "slurm" | "unscheduled" ) break ;;
            * ) echo "Please respond with one of the listed options. Input is case sensitive. (lsf, slurm, unscheduled) " ;;
    esac
done

# Assign Default Values
n_procs="${n_procs:=4}"
n_iters="${n_iters:=1}"
msg_sizes="${msg_sizes:=512}"
n_nodes="${n_nodes:=1}"
run_count="${run_count:=2}"
results_path="${results_path:=$HOME/comm_pattern_output/${comm_pattern}_$(date +%s.%N)/}"
if [ ${scheduler} != "slurm" ]; then
    slurm_queue=""
    slurm_time_limit=""
fi

# Report Variable Values
echo "Communication Pattern: ${comm_pattern}"
echo "Scheduler Selected: ${scheduler}"
echo "Number of Processes: ${n_procs}"
echo "Number of Iterations: ${n_iters}"
echo "Message Size: ${msg_sizes}"
echo "Number of Nodes: ${n_nodes}"
echo "Queue for Running through Slurm: ${slurm_queue}"
echo "Time Limit for Running through Slurm: ${slurm_time_limit}"
echo "Number of Execution Runs: ${run_count}"
echo "Output will be stored in ${results_path}"




# Define Needed Paths
cd apps/comm_pattern_generator/${scheduler}
example_paths_dir=$(pwd)
cd -
source ${example_paths_dir}/example_paths_${scheduler}.config
config_path=${anacin_x_root}/apps/comm_pattern_generator/config
comm_pattern_path=${anacin_x_root}/apps/comm_pattern_generator/${scheduler}


# Run Comm Pattern Script
#for n_iters in ${num_iters[@]};
#do
#    for n_procs in ${num_procs[@]};
#    do
#	for msg_sizes in ${message_sizes[@]};
#	do
if [ ${comm_pattern} == "message_race" ]; then
    bash ${comm_pattern_path}/${comm_pattern}_${scheduler}.sh ${n_procs} ${n_iters} ${msg_sizes} ${n_nodes} ${slurm_queue} ${slurm_time_limit} 0 $((run_count-1)) ${results_path} ${example_paths_dir}
elif [ ${comm_pattern} == "amg2013" ]; then
    bash ${comm_pattern_path}/${comm_pattern}_${scheduler}.sh ${n_procs} ${n_iters} ${msg_sizes} ${n_nodes} ${slurm_queue} ${slurm_time_limit} 0 $((run_count-1)) ${results_path} ${example_paths_dir}
elif [ ${comm_pattern} == "unstructured_mesh" ]; then
    bash ${comm_pattern_path}/${comm_pattern}_${scheduler}.sh ${n_procs} ${n_iters} ${msg_sizes} ${n_nodes} ${slurm_queue} ${slurm_time_limit} 0 $((run_count-1)) ${results_path} ${example_paths_dir}
fi
#	done
#    done
#done
