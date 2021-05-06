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
    echo "[-p]    Defines the size of the mpi communicator used when generating communication patterns. (Default 10 MPI processes)"
    echo "[-i]    Defines the number of times a given communication pattern appears in a single execution of ANACIN-X. (Default 1 iteration)"
    echo "[-s]    The size in bytes of the messages passed when generating communication patterns. (Default 512 bytes)"
    echo "[-n]    The number of compute nodes requested for running the ANACIN-X workflow. (Default 1 node)"
    echo "[-r]    The number of runs to make of the ANACIN-X workflow. (Default 2 executions)"
    echo "        The number of runs must be at least 2"
    echo "[-o]    If used, allows the user to define their own path to store output from the project. (Defaults to the directory '$HOME/comm_pattern_output')"
    echo "[-c]    When running the unstructured mesh communication pattern, use this with 3 arguments to define the grid coordinates. (Ex. -c 2 3 4)"
    echo "        The 3 coordinate values must multiply together to equal the number of processes used."
    echo "        The 3 coordinate values must also multiply together to be greater than or equal 10."
    echo "[-v]    If used, will display the execution settings prior to running the execution."
    echo "[-h]    Used to display the list of switch options."
    echo ""
    echo "If you're running on a system that uses the Slurm scheduler, then the following switches can be used to define settings for job submission:"
    echo "[-sq]   Defines the queue to submit Slurm jobs to. (Defaults to the "normal" queue)"
    echo "[-st]   A maximum time limit in minutes on the time provided to jobs submitted. (Default 10 minutes)"
    echo ""
    echo "If you're running on a system that uses the LSF scheduler, then the following switches can be used to define settings for job submission:"
    echo "[-lq]   Defines the queue to submit LSF jobs to. (Defaults to the "normal" queue)"
    echo "[-lt]   A maximum time limit in minutes on the time provided to jobs submitted. (Default 10 minutes)"
    echo ""
}


while [ -n "$1" ]; do
    case "$1" in
	    -p)  n_procs=$2; shift; shift ;;
	    -i)  n_iters=$2; shift; shift ;;
	    -s)  msg_sizes=$2; shift; shift ;;
	    -n)  n_nodes=$2; shift; shift ;; 
	    -sq) slurm_queue=$2; shift; shift ;;
	    -st) slurm_time_limit=$2; shift; shift ;;
	    -lq) lsf_queue=$2; shift; shift ;;
            -lt) lsf_time_limit=$2; shift; shift ;;
	    -r)  run_count=$2; shift; shift ;;
	    -o)  results_path=$2; shift; shift ;;
	    -c)  x_procs=$2; y_procs=$3; z_procs=$4; shift; shift; shift; shift ;;
	    -v)  verbose="true"; shift ;;
	    -h)  Help; exit ;;
	    *)   echo "$1 is not an option"; exit ;;
    esac
done


# Comm Pattern definition
while true; do
    read -p "Which communication pattern would you like to analyze? Input is case sensitive. (message_race, amg2013, unstructured_mesh) " comm_pattern
    case ${comm_pattern} in
	    "message_race" | "amg2013" | "unstructured_mesh" ) break ;;
	    * ) echo "Please respond with one of the listed options. Input is case sensitive. (message_race, amg2013, unstructured_mesh) " ;;
    esac
done

# Ensure that input values will work
while [ ${comm_pattern} == "unstructured_mesh" ] && [ $(( x_procs*y_procs*z_procs )) -lt 10 ]; do
    echo "The 3 coordinate values of unstructured mesh must multiply together to be greater than or equal to 10."
    echo "Note that the product of these values will need to be equal to the number of processes."
    read -p "x coordinate: " x_procs
    read -p "y coordinate: " y_procs
    read -p "z coordinate: " z_procs
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
n_procs="${n_procs:=10}"
if [ ${comm_pattern} == "unstructured_mesh" ] && [ $(( x_procs*y_procs*z_procs )) -ne ${n_procs} ]; then
    echo "The number of processes must correspond to the product of the unstructured mesh coordinates ${x_procs}, ${y_procs}, and ${z_procs}"
    echo "Updating the number of processes to $(( x_procs*y_procs*z_procs )) = ${x_procs}*${y_procs}*${z_procs}"
    n_procs=$(( x_procs*y_procs*z_procs ))
fi
n_iters="${n_iters:=1}"
msg_sizes="${msg_sizes:=512}"
n_nodes="${n_nodes:=1}"
run_count="${run_count:=2}"
results_path="${results_path:=$HOME/comm_pattern_output/${comm_pattern}_$(date +%s)/}"
if [ ${scheduler} == "slurm" ]; then
    slurm_queue="${slurm_queue:="normal"}"
    slurm_time_limit="${slurm_time_limit:=10}"
else
    slurm_queue=""
    slurm_time_limit=""
fi
if [ ${scheduler} == "lsf" ]; then
    lsf_queue="${lsf_queue:="normal"}"
    lsf_time_limit="${lsf_time_limit:=10}"
else
    lsf_queue=""
    lsf_time_limit=""
fi

# Report Variable Values if User Requests Verbose Execution
if [ "${verbose}" == "true" ]; then
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
    if [ ${scheduler} == "lsf" ]; then
        echo "Queue for Running through LSF: ${lsf_queue}"
        echo "Time Limit for Running through LSF: ${lsf_time_limit}"
    fi
    echo "Number of Execution Runs: ${run_count}"
    if [ ${comm_pattern} == "unstructured_mesh" ]; then
        echo "Unstructured Mesh Coordinates x*y*z = ${x_procs}*${y_procs}*${z_procs}"
    fi
    echo "Output will be stored in ${results_path}"
fi




# Define Needed Paths
cd apps/comm_pattern_generator/${scheduler}
example_paths_dir=$(pwd)
cd -
source ${example_paths_dir}/example_paths_${scheduler}.config
config_path=${anacin_x_root}/apps/comm_pattern_generator/config
comm_pattern_path=${anacin_x_root}/apps/comm_pattern_generator/${scheduler}


# Copy Run Configuration into Output Files
mkdir -p ${results_path}
user_config_file=${results_path}/comm_pattern_config.txt
cp ${graph_kernel} ${results_path}
echo "Communication Pattern: ${comm_pattern}" >> ${user_config_file}
echo "Scheduler Selected: ${scheduler}" >> ${user_config_file}
echo "Number of Processes: ${n_procs}" >> ${user_config_file}
echo "Number of Iterations: ${n_iters}" >> ${user_config_file}
echo "Message Size: ${msg_sizes}" >> ${user_config_file}
echo "Number of Nodes: ${n_nodes}" >> ${user_config_file}
if [ ${scheduler} == "slurm" ]; then
    echo "Queue for Running through Slurm: ${slurm_queue}" >> ${user_config_file}
    echo "Time Limit for Running through Slurm: ${slurm_time_limit}" >> ${user_config_file}
fi
if [ ${scheduler} == "lsf" ]; then
    echo "Queue for Running through LSF: ${lsf_queue}" >> ${user_config_file}
    echo "Time Limit for Running through LSF: ${lsf_time_limit}" >> ${user_config_file}
fi
echo "Number of Execution Runs: ${run_count}" >> ${user_config_file}
if [ ${comm_pattern} == "unstructured_mesh" ]; then
    echo "Unstructured Mesh Coordinates x*y*z = ${x_procs}*${y_procs}*${z_procs}" >> ${user_config_file}
fi
echo "Output will be stored in ${results_path}" >> ${user_config_file}


# Run Comm Pattern Script
if [ ${comm_pattern} == "message_race" ]; then
    bash ${comm_pattern_path}/${comm_pattern}_${scheduler}.sh ${n_procs} ${n_iters} ${msg_sizes} ${n_nodes} ${slurm_queue} ${slurm_time_limit} ${lsf_queue} ${lsf_time_limit} 0 $((run_count-1)) ${results_path} ${example_paths_dir}
    echo "Stored kernel distance data in output file ${results_path}/msg_size_${msg_sizes}/n_procs_${n_procs}/n_iters_${n_iters}/kdts.pkl"
elif [ ${comm_pattern} == "amg2013" ]; then
    bash ${comm_pattern_path}/${comm_pattern}_${scheduler}.sh ${n_procs} ${n_iters} ${msg_sizes} ${n_nodes} ${slurm_queue} ${slurm_time_limit} ${lsf_queue} ${lsf_time_limit} 0 $((run_count-1)) ${results_path} ${example_paths_dir}
    echo "Stored kernel distance data in output file ${results_path}/msg_size_${msg_sizes}/n_procs_${n_procs}/n_iters_${n_iters}/kdts.pkl"
elif [ ${comm_pattern} == "unstructured_mesh" ]; then
    bash ${comm_pattern_path}/${comm_pattern}_${scheduler}.sh ${n_procs} ${n_iters} ${msg_sizes} ${n_nodes} ${slurm_queue} ${slurm_time_limit} ${lsf_queue} ${lsf_time_limit} 0 $((run_count-1)) ${results_path} ${example_paths_dir} ${x_procs} ${y_procs} ${z_procs}
    echo "Stored kernel distance data in output file ${results_path}/msg_size_${msg_sizes}/n_procs_${n_procs}/n_iters_${n_iters}/proc_placement_pack/nd_neighbor_fraction_{0, 0.25, 0.5, 0.75, 1}/kdts.pkl"
fi


# Communicate where to find visualization files
echo "Used the communication pattern type: ${comm_pattern}"
echo "Used graph kernel JSON file:         ${graph_kernel}"



