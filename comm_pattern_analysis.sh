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


Help() {
    echo ""
    echo "Below are the switches available to use when running this script"
    echo ""
    echo "The following command line switches can be used to define parameters for your job submission:"
echo "* -p : Defines the size of the mpi communicator used when generating communication patterns. (Default 4 MPI processes)"
echo "* -i : Defines the number of times a given communication pattern appears in a single execution of ANACIN-X. (Default 1 iteration)"
echo "* -s : The size in bytes of the messages passed when generating communication patterns. (Default 512 bytes)"
echo "* -n : The number of compute nodes requested for running the ANACIN-X workflow. (Default 1 node)"
echo "* -r : The number of runs to make of the ANACIN-X workflow. (Default 2 executions)"
echo "* -o : If used, allows the user to define their own path to store output from the project. (Defaults to the directory '$HOME/comm_pattern_output')"
echo "* -v : If used, will display the execution settings prior to running the execution."
echo "* -h : Used to display the list of switch options."
echo ""
echo "If you're running on a system that uses the Slurm scheduler, then the following switches can be used to define settings for job submission:"
echo "* -sq : Defines the queue to submit Slurm jobs to. (Defaults to the "normal" queue)"
echo "* -st : A maximum time limit in minutes on the time provided to jobs submitted. (Default 10 minutes)"
echo ""
}


while [ -n "$1" ]; do
    case "$1" in
	    -p) n_procs=$2; shift; shift ;;
	    -i) n_iters=$2; shift; shift ;;
	    -s) msg_sizes=$2; shift; shift ;;
	    -n) n_nodes=$2; shift; shift ;; 
	    -sq) slurm_queue=$2; shift; shift ;;
	    -st) slurm_time_limit=$2; shift; shift ;;
	    -lq) lsf_queue=$2; shift; shift ;;
	    -r) run_count=$2; shift; shift ;;
	    -o) results_path=$2; shift; shift ;;
	    -v) verbose="true"; shift ;;
	    -h) Help; exit ;;
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
if [ ${scheduler} == "slurm" ]; then
    slurm_queue="normal"
    slurm_time_limit="10"
else
    slurm_queue=""
    slurm_time_limit=""
fi

# Report Variable Values if User Requests Verbose Execution
if [ ${verbose} == "true" ]; then
    echo "Communication Pattern: ${comm_pattern}"
    echo "Scheduler Selected: ${scheduler}"
    echo "Number of Processes: ${n_procs}"
    echo "Number of Iterations: ${n_iters}"
    echo "Message Size: ${msg_sizes}"
    echo "Number of Nodes: ${n_nodes}"
    if [ ${scheduler} == "slurm" ]; then
        echo "Queue for Running through Slurm: ${slurm_queue}"
        echo "Time Limit for Running through Slurm: ${slurm_time_limit}"
    fi
    echo "Number of Execution Runs: ${run_count}"
    echo "Output will be stored in ${results_path}"
fi




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
