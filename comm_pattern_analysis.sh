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
    echo "        If you're running the message race communication pattern, it's recommended to set this to at least 10."
    echo "[-s]    The size in bytes of the messages passed when generating communication patterns. (Default 512 bytes)"
    echo "[-n]    The number of compute nodes requested for running the ANACIN-X workflow. (Default 1 node)"
    echo "        If you're running on an unscheduled system, this value should be set to 1."
    echo "[-r]    The number of runs to make of the ANACIN-X workflow. (Default 2 executions)"
    echo "        The number of runs must be at least 2"
    echo "[-o]    If used, allows the user to define their own path to store output from the project. (Defaults to the directory '$HOME/comm_pattern_output')"
    echo "        When using this flag, be sure to provide an absolute path that can exist on your machine."
    echo "        If you run this script multiple times on the same settings, be sure to use different paths to avoid overlap and overwriting of files."
    echo "[-c]    When running the unstructured mesh communication pattern, use this with 3 arguments to define the grid coordinates. (Ex. -c 2 3 4)"
    echo "        The 3 coordinate values must multiply together to equal the number of processes used."
    echo "        The 3 coordinate values must also multiply together to be greater than or equal 10."
    echo "[-v]    If used, will display the execution settings prior to running the execution."
    echo "[-h]    Used to display the list of switch options."
    echo "[-nd]   Takes 3 arguments in decinal format (start percent, step size, end percent) to define message non-determinism percentages present in the final data."
    echo "        Start percent and end percent are the lowest and highest percentages used respectively.  The step size defines the percentages in between."
    echo "        For example, default values correspond to '-nd 0.0 0.1 1.0'. The percentages used from this are 0, 10, 20, 30, ..., 100"
    echo "        All 3 values must fall between 0 and 1, inclusive, and must satisfy the relationship 'start percent + step size * step count = end percent'."
    echo "[-nt]   When running the unstructured mesh communication pattern, takes the percentage of topological non-determinism in decimal format."
    echo "        For example, default values corresopnd to '-nt 0.5'."
    echo "        Value must fall in the range of 0 to 1, inclusive."
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
	    -nd) nd_start=$2; nd_iter=$3; nd_end=$4; shift; shift; shift; shift ;;
	    -nt) nd_topo=$2; shift; shift ;;
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
nd_start="${nd_start:=0.0}"
nd_iter="${nd_iter:=0.1}"
nd_end="${nd_end:=1.0}"
nd_topo="${nd_topo:=0.5}"
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

# Ensure ND% values are valid, between 0 and 1, satisfy iteration condition
while (( $(echo "$nd_start < 0" |bc -l) || $(echo "$nd_start > 1" |bc -l) || $(echo "$nd_iter < 0" |bc -l) || $(echo "$nd_iter > 1" |bc -l) || $(echo "$nd_end < 0" |bc -l) || $(echo "$nd_end < 0" |bc -l) || $(echo "$nd_end > 1" |bc -l) )); do
	echo "The 3 values defining non-determinism percentage are not all between 0 and 1."
	echo "Please set these values between 0 and 1, inclusive."
	read -p "Starting Non-determinism Percentage: " nd_start
	read -p "Non-determinism Percentage Step Size: " nd_iter
	read -p "Ending Non-determinism Percentage: " nd_end
done
ndp_step_count=$(echo "scale=1; ($nd_end - $nd_start)/$nd_iter" |bc -l)
while ! [[ "$ndp_step_count" =~ ^[0-9]+[.][0]$ ]]; do
	echo "Your non-determinism percentage defining values do not satisfy the needed constraints."
	echo "Please ensure that they satisfy: start percent + step size * step count = end percent."
	read -p "start percent: " nd_start
	read -p "step size: " nd_iter
	read -p "end percent: " nd_end
done
while [ ${comm_pattern} == "unstructured_mesh" ] && (( $(echo "$nd_topo < 0" |bc -l) || $(echo "$nd_topo > 1" |bc -l) )); do
	echo "The topological non-determinism percentage is not between 0 and 1."
	echo "Please set this value between 0 and 1, inclusive."
	read -p "Topological Non-determinism Percentage: " nd_topo
done

# Ensure the output path is a valid path.
project_path=$(pwd)
cd
while true; do
    case "${results_path}" in
        /*) mkdir -p ${results_path} 
		if [[ -d "${results_path}" ]]; then
		    break
		else
		    echo "Your output path is not a valid path.  Please make sure that the path you provided can exist on your machine."
		    echo "As an example, you might input something of the form "$(pwd)"/example_path"
		    read -p "Input your path here: " results_path
		fi ;;
	*)  echo "Your output path is not an absolute path.  Please make sure to input an absolute path for your output. It should start with a '/' character."
		echo "As an example, you might input something of the form "$(pwd)"/example_path" 
		read -p "Input your path here: " results_path ;;
    esac
done
cd ${project_path}

# Report Variable Values if User Requests Verbose Execution
if [ "${verbose}" == "true" ]; then
    echo "Communication Pattern: ${comm_pattern}"
    echo "Scheduler Selected: ${scheduler}"
    echo "Number of Processes: ${n_procs}"
    echo "Number of Iterations: ${n_iters}"
    echo "Message Size: ${msg_sizes}"
    echo "Number of Nodes: ${n_nodes}"
    echo "Starting Non-determinism Percentage: ${nd_start}"
    echo "Non-determinism Percentage Step Size: ${nd_iter}"
    echo "Ending Non-determinism Percentage: ${nd_end}"
    echo "Topological Non-determinism Percentage ${nd_topo}"
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
cd ${project_path}
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
echo "Starting Non-determinism Percentage: ${nd_start}" >> ${user_config_file}
echo "Non-determinism Percentage Step Size: ${nd_iter}" >> ${user_config_file}
echo "Ending Non-determinism Percentage: ${nd_end}" >> ${user_config_file}
echo "Topological Non-determinism Percentage: ${nd_topo}" >> ${user_config_file}
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
    bash ${comm_pattern_path}/${comm_pattern}_${scheduler}.sh ${n_procs} ${n_iters} ${msg_sizes} ${n_nodes} ${slurm_queue} ${slurm_time_limit} ${lsf_queue} ${lsf_time_limit} 0 $((run_count-1)) ${results_path} ${example_paths_dir} ${nd_start} ${nd_iter} ${nd_end}
    echo "Stored kernel distance data in output file: ${results_path}/msg_size_${msg_sizes}/n_procs_${n_procs}/n_iters_${n_iters}/ndp_${nd_start}_${nd_iter}_${nd_end}/kdts.pkl"
elif [ ${comm_pattern} == "amg2013" ]; then
    bash ${comm_pattern_path}/${comm_pattern}_${scheduler}.sh ${n_procs} ${n_iters} ${msg_sizes} ${n_nodes} ${slurm_queue} ${slurm_time_limit} ${lsf_queue} ${lsf_time_limit} 0 $((run_count-1)) ${results_path} ${example_paths_dir} ${nd_start} ${nd_iter} ${nd_end}
    echo "Stored kernel distance data in output file: ${results_path}/msg_size_${msg_sizes}/n_procs_${n_procs}/n_iters_${n_iters}/ndp_${nd_start}_${nd_iter}_${nd_end}/kdts.pkl"
elif [ ${comm_pattern} == "unstructured_mesh" ]; then
    bash ${comm_pattern_path}/${comm_pattern}_${scheduler}.sh ${n_procs} ${n_iters} ${msg_sizes} ${n_nodes} ${slurm_queue} ${slurm_time_limit} ${lsf_queue} ${lsf_time_limit} 0 $((run_count-1)) ${results_path} ${example_paths_dir} ${x_procs} ${y_procs} ${z_procs} ${nd_start} ${nd_iter} ${nd_end} ${nd_topo}
    echo "Stored kernel distance data in output file: ${results_path}/msg_size_${msg_sizes}/n_procs_${n_procs}/n_iters_${n_iters}/ndp_${nd_start}_${nd_iter}_${nd_end}/proc_placement_pack/neighbor_nd_fraction_${nd_topo}/kdts.pkl"
fi


# Communicate where to find visualization files
echo "Used the communication pattern type:        ${comm_pattern}"
echo "Used graph kernel JSON file:                ${graph_kernel}"
echo "Starting non-determinism percentage:        ${nd_start}"
echo "Non-determinism percentage step size:       ${nd_iter}"
echo "Ending non-determinism percentage:          ${nd_end}"
echo "Topological non-determinism percentage:     ${nd_topo}"


