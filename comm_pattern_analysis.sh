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
    echo "[-p]    Defines the number of mpi processes used when generating communication patterns. (Default 10 MPI processes)"
    echo "[-i]    Defines the number of times a given communication pattern appears in a single execution of ANACIN-X. (Default 1 iteration)"
    echo "        If you're running the message race communication pattern, it's recommended to set this to at least 10."
    echo "[-s]    The size in bytes of the messages passed when generating communication patterns. (Default 512 bytes)"
    echo "[-n]    The number of compute nodes requested for running the ANACIN-X workflow. (Default 1 node)"
    echo "        If you're running on an unscheduled system, this value should be set to 1."
    echo "[-r]    The number of runs to make of the ANACIN-X workflow. (Default 2 executions)"
    echo "        The number of runs must be at least 2"
    echo "[-cp]   Used to define the communication pattern benchmark for testing. (Code will request this if not set)"
    echo "        Must be one of the 3 provided benchmarks in the following format: message_race, amg2013, or unstructured_mesh."
    echo "[-sc]   Used to define which schedule system is currently in use. (Code will request this if not set)"
    echo "        Must be one of the following options: lsf, slurm, or unscheduled."
    #echo "[-cs]   If used, then callstack tracing will be activated.  Doesn't take any arguments."
    echo "[-o]    If used, allows the user to define their own path to store output from the project. (Defaults to the directory '$HOME/comm_pattern_output')"
    echo "        When using this flag, be sure to provide an absolute path that can exist on your machine."
    echo "        If you run this script multiple times on the same settings, be sure to use different paths to avoid overlap and overwriting of files."
    echo "[-c]    When running the unstructured mesh communication pattern, use this with 3 arguments to define the grid coordinates. (Ex. -c 2 3 4)"
    echo "        The 3 coordinate values must be integers greater than 1 and multiply together to equal the number of processes used."
    echo "        The 3 coordinate values must also multiply together to be greater than or equal 10."
    echo "[-ct]   Defines the tool to use during callstack backtracing. (Defaults to "glibc")"
    echo "        The options for this are "glibc" and "libunwind"."
    echo "[-v]    If used, will display the execution settings prior to running the execution."
    echo "[-h]    Used to display the list of switch options."
    echo "[-nd]   Takes 3 arguments in decinal format (start percent, step size, end percent) to define message non-determinism percentages present in the final data."
    echo "        Start percent and end percent are the lowest and highest percentages used respectively.  The step size defines the percentages in between."
    echo "        For example, default values correspond to '-nd 0.0 0.1 1.0'. The percentages used from this are 0, 10, 20, 30, ..., 100"
    echo "        All 3 values must fall between 0 and 1, inclusive, and must satisfy the relationship 'start percent + step size * step count = end percent'."
    echo "        All 3 values must also contain no more than 2 digits past the decimal."
    echo "[-nt]   When running the unstructured mesh communication pattern, takes the percentage of topological non-determinism in decimal format."
    echo "        For example, default values corresopnd to '-nt 0.5'."
    echo "        Value must fall in the range of 0 to 1, inclusive."
    echo ""
    echo "If you're running on a scheduled system, then the following switches can be used to define settings for job submission:"
    echo "[-q]    Defines the queue to submit jobs to. (Defaults to the "normal" queue)"
    echo "[-t]    A maximum time limit in minutes on the time provided for communication pattern runs. (Default 10 minutes)"
#    echo "If you're running on a system that uses the Slurm scheduler, then the following switches can be used to define settings for job submission:"
#    echo "[-sq]   Defines the queue to submit Slurm jobs to. (Defaults to the "normal" queue)"
#    echo "[-st]   A maximum time limit in minutes on the time provided to jobs submitted. (Default 10 minutes)"
#    echo ""
#    echo "If you're running on a system that uses the LSF scheduler, then the following switches can be used to define settings for job submission:"
#    echo "[-lq]   Defines the queue to submit LSF jobs to. (Defaults to the "normal" queue)"
#    echo "[-lt]   A maximum time limit in minutes on the time provided to jobs submitted. (Default 10 minutes)"
#    echo ""

}


while [ -n "$1" ]; do
    case "$1" in
	    -p)  n_procs=$2; shift; shift ;;
	    -i)  n_iters=$2; shift; shift ;;
	    -s)  msg_sizes=$2; shift; shift ;;
	    -n)  n_nodes=$2; shift; shift ;; 
	    #-sq) slurm_queue=$2; shift; shift ;;
	    #-st) slurm_time_limit=$2; shift; shift ;;
	    #-lq) lsf_queue=$2; shift; shift ;;
            #-lt) lsf_time_limit=$2; shift; shift ;;
	    -q)  queue=$2; shift; shift ;;
	    -t)  time_limit=$2; shift; shift ;;
	    #-cs) run_csmpi="True"; shift ;;
	    -r)  run_count=$2; shift; shift ;;
	    -o)  results_path=$2; shift; shift ;;
	    -c)  x_procs=$2; y_procs=$3; z_procs=$4; shift; shift; shift; shift ;;
	    -ct) impl=$2; shift; shift ;;
	    -cp) comm_pattern=$2; shift; shift ;;
	    -sc) scheduler=$2; shift; shift ;;
	    -nd) nd_start=$2; nd_iter=$3; nd_end=$4; shift; shift; shift; shift ;;
	    -nt) nd_topo=$2; shift; shift ;;
	    -v)  verbose="true"; shift ;;
	    -h)  Help; exit ;;
	    *)   echo "$1 is not an option"; exit ;;
    esac
done


# Comm Pattern definition
while true; do
    #read -p "Which communication pattern would you like to analyze? Input is case sensitive. (message_race, amg2013, unstructured_mesh) " comm_pattern
    case ${comm_pattern} in
	    "message_race" | "amg2013" | "unstructured_mesh" ) break ;;
	    #* ) echo "Please respond with one of the listed options. Input is case sensitive. (message_race, amg2013, unstructured_mesh) " ;;
	    * ) echo "The communication pattern must be selected from one of the provided benchmarks."
		read -p "Please select one of the three provided options. Input is case sensitive. (message_race, amg2013, unstructured_mesh) " comm_pattern ;;
    esac
done

# Pick a scheduler
while true; do
    #read -p "Which job scheduler would you like to use? Input is case sensitive. (lsf, slurm, unscheduled) " scheduler
    case ${scheduler} in
            "lsf" | "slurm" | "unscheduled" ) break ;;
            * ) echo "The scheduler system needs to be selected from one of the three optional schedulers. (lsf, slurm, unscheduled) "
		read -p "Please respond with one of the listed options. Input is case sensitive. " scheduler ;;
    esac
done

# Notify user of unused values
if [ ${comm_pattern} != "unstructured_mesh" ] && ( [ ! -z ${x_procs} ] || [ ! -z ${y_procs} ] || [ ! -z ${z_procs} ] ) ; then
        echo "Warning: the Unstructured Mesh grid size has been set. These values will not be used for the selected communication pattern - ${comm_pattern}"
fi
if [ ${comm_pattern} != "unstructured_mesh" ] && [ ! -z ${nd_topo} ] ; then
        echo "Warning: the Unstructured Mesh topological non-determinism percentage has been set.  This value will not be used for the selected commnication pattern - ${comm_pattern}"
fi


# Assign Default Values
n_procs="${n_procs:=10}"
comm_pattern="${comm_pattern:="message_race"}"
scheduler="${scheduler:="unscheduled"}"
n_iters="${n_iters:=1}"
msg_sizes="${msg_sizes:=512}"
n_nodes="${n_nodes:=1}"
run_count="${run_count:=2}"
nd_start="${nd_start:=0.0}"
nd_iter="${nd_iter:=0.1}"
nd_end="${nd_end:=1.0}"
#run_csmpi="${run_csmpi:="False"}"
impl="${impl:="glibc"}"
nd_topo="${nd_topo:=0.5}"
results_path="${results_path:=$HOME/comm_pattern_output/${comm_pattern}_$(date +%s)/}"
#if [ ${scheduler} == "slurm" ]; then
#    slurm_queue="${slurm_queue:="normal"}"
#    slurm_time_limit="${slurm_time_limit:=10}"
#else
#    slurm_queue=""
#    slurm_time_limit=""
#fi
queue="${queue:="normal"}"
time_limit="${time_limet:=10}"
#if [ ${scheduler} == "lsf" ]; then
#    lsf_queue="${lsf_queue:="normal"}"
#    lsf_time_limit="${lsf_time_limit:=10}"
#else
#    lsf_queue=""
#    lsf_time_limit=""
#fi

# Ensure ND% values are valid, between 0 and 1, satisfy iteration condition
#ndp_step_count=$(echo "scale=1; ($nd_end - $nd_start)/$nd_iter" |bc -l)
#while (( $(echo "$nd_start < 0" |bc -l) || $(echo "$nd_start > 1" |bc -l) || $(echo "$nd_iter < 0" |bc -l) || $(echo "$nd_iter > 1" |bc -l) || $(echo "$nd_end < 0" |bc -l) || $(echo "$nd_end < 0" |bc -l) || $(echo "$nd_end > 1" |bc -l) )); do
while true; do
	if (( $(echo "$nd_start < 0" |bc -l) || $(echo "$nd_start > 1" |bc -l) || $(echo "$nd_iter < 0" |bc -l) || $(echo "$nd_iter > 1" |bc -l) || $(echo "$nd_end < 0" |bc -l) || $(echo "$nd_end > 1" |bc -l) )) || [ -z "$nd_start" ] || [ -z "$nd_iter" ] || [ -z "$nd_end" ]; then
		echo "The 3 values defining non-determinism percentage are not all between 0 and 1 or are not all set."
		echo "They are currecntly set to: ${nd_start} ${nd_iter} ${nd_end}"
		echo "Please set these values between 0 and 1, inclusive."
		read -p "Starting Non-determinism Percentage: " nd_start
		read -p "Non-determinism Percentage Step Size: " nd_iter
		read -p "Ending Non-determinism Percentage: " nd_end
	fi
	if (( $(echo "$nd_iter == 0.0" |bc -l) )); then
		ndp_step_count=0.0;
	else
		ndp_step_count=$(echo "scale=1; ($nd_end - $nd_start)/$nd_iter" |bc -l)
	fi
	if ! [[ "$ndp_step_count" =~ ^[0-9]+[.][0]$ ]] || [ -z "$nd_start" ] || [ -z "$nd_iter" ] || [ -z "$nd_end" ]; then
		echo "Your non-determinism percentage defining values do not satisfy the needed following constraint or are not all set."
		echo "They are currecntly set to: ${nd_start} ${nd_iter} ${nd_end}"
        	echo "Please ensure that they satisfy: start percent + step size * step count = end percent."
        	read -p "Starting Non-determinism Percentage: " nd_start
        	read -p "Non-determinism Percentage Step Size: " nd_iter
        	read -p "Ending Non-determinism Percentage: " nd_end
	fi
        if (( $(echo "$nd_iter == 0.0" |bc -l) )); then
                ndp_step_count=0.0;
        else
                ndp_step_count=$(echo "scale=1; ($nd_end - $nd_start)/$nd_iter" |bc -l)
        fi
	if ! (( $(echo "$nd_start < 0" |bc -l) || $(echo "$nd_start > 1" |bc -l) || $(echo "$nd_iter < 0" |bc -l) || $(echo "$nd_iter > 1" |bc -l) || $(echo "$nd_end < 0" |bc -l) || $(echo "$nd_end > 1" |bc -l) )) && [[ "$ndp_step_count" =~ ^[0-9]+[.][0]$ ]] && ! [ -z "$nd_start" ] && ! [ -z "$nd_iter" ] && ! [ -z "$nd_end" ]; then
		break;
	fi
done
if [[ "$nd_start" =~ ^[0-9]+[.][0-9][0-9][0-9]*$ ]] || [[ "$nd_iter" =~ ^[0-9]+[.][0-9][0-9][0-9]*$ ]] || [[ "$nd_end" =~ ^[0-9]+[.][0-9][0-9][0-9]*$ ]]; then
	echo "Warning: The values defining message non-determinism have been set with too many decimal points."
	echo "The 3 values will be adjusted to 2 decimal points of precision, per program requirements."
	nd_start=$(printf "%.2f\n" "$nd_start")
	nd_iter=$(printf "%.2f\n" "$nd_iter")
	nd_end=$(printf "%.2f\n" "$nd_end")
	echo "They will now be set to: ${nd_start} ${nd_iter} ${nd_end}"
fi
if (( $(echo "$nd_iter == 0.0" |bc -l) && $(echo "$nd_end > $nd_start" |bc -l) )); then
	echo "Warning: You have requested that the non-determinism percentage step size be 0.0 and that the final non-determinism percentage be different from the starting non-determinism percentage."
	echo "         The requested final non-determinism percentage will not be used because the step size is 0.0."
fi
while [ ${comm_pattern} == "unstructured_mesh" ] && ( (( $(echo "$nd_topo < 0" |bc -l) || $(echo "$nd_topo > 1" |bc -l) )) || [ -z "$nd_topo" ] ); do
	echo "The topological non-determinism percentage is not between 0 and 1 or is not set."
	echo "Please set this value between 0 and 1, inclusive."
	read -p "Topological Non-determinism Percentage: " nd_topo
done

# Ensure the input values are valid to program requirements
while (( $(echo "$n_procs < 1" |bc -l) )) || ! [[ "$n_procs" =~ ^[0-9]+$ ]] || [ -z "$n_procs" ] ; do
	echo "Number of MPI processes was set too low or is not an integer."
	echo "Please set number of processes to an integer greater than 0. We recommend using at least 10 if available."
	read -p "Number of MPI processes requested: " n_procs
done
while [ ${comm_pattern} == "unstructured_mesh" ] && ( ! [[ "$x_procs" =~ ^[0-9]+$ ]] || ! [[ "$y_procs" =~ ^[0-9]+$ ]] || ! [[ "$z_procs" =~ ^[0-9]+$ ]] || (( $(echo "$x_procs < 2" |bc -l) )) || (( $(echo "$y_procs < 2" |bc -l) )) || (( $(echo "$z_procs < 2" |bc -l) )) || [ $(( x_procs*y_procs*z_procs )) -lt 10 ] || [ -z "$x_procs" ] || [ -z "$y_procs" ] || [ -z "$z_procs" ] ) ; do
        echo "The 3 coordinate values of unstructured mesh currently multiply together to equal x_procs*y_procs*z_procs=$(echo "$x_procs * $y_procs * $z_procs" |bc -l)"
        echo "The 3 value must be integers greater than 1 and multiply together to be greater than or equal to 10."
        echo "Please adjust each coordinate so that they satisfy the conditions."
        read -p "x coordinate: " x_procs
        read -p "y coordinate: " y_procs
        read -p "z coordinate: " z_procs
done
if [ ${comm_pattern} == "unstructured_mesh" ] && [ $(( x_procs*y_procs*z_procs )) -ne ${n_procs} ]; then
	echo "The 3 coordinate values of unstructured mesh must multiply together to equal the number of MPI processes requested."
	echo "The 3 values currently multiply together to equal x_procs*y_procs*z_procs=$(( x_procs*y_procs*z_procs ))"
	echo "Updating the number of processes to $(( x_procs*y_procs*z_procs )) = ${x_procs}*${y_procs}*${z_procs}"
	n_procs=$(( x_procs*y_procs*z_procs ))
fi
while (( $(echo "$n_iters < 1" |bc -l) )) || ! [[ "$n_iters" =~ ^[0-9]+$ ]] || [ -z "$n_iters" ] ; do
        echo "Number of communication pattern iterations was set too low or is not an integer."
        echo "Please set number of iterations to an integer greater than 0. We recommend using at least 5."
        read -p "Number of iterations requested: " n_iters
done
while (( $(echo "$n_nodes < 1" |bc -l) )) || ! [[ "$n_nodes" =~ ^[0-9]+$ ]] || [ -z "$n_nodes" ] ; do
        echo "Number of compute nodes was set too low or is not an integer."
        echo "Please set number of compute nodes to an integer greater than 0. We recommend using at least 2 if available."
        read -p "Number of compute nodes requested: " n_nodes
done
while (( $(echo "$msg_sizes < 1" |bc -l) )) || ! [[ "$msg_sizes" =~ ^[0-9]+$ ]] || [ -z "$msg_sizes" ] ; do
        echo "The size of messages to use was set too low or is not an integer."
        echo "Please set the message size to an integer greater than 0."
        read -p "Message size requested: " msg_sizes
done
while (( $(echo "$run_count < 2" |bc -l) )) || (( $(echo "$run_count > 999" |bc -l) )) || ! [[ "$run_count" =~ ^[0-9]+$ ]] || [ -z "$run_count" ] ; do
        echo "Number of simulation executions was set too low or is not an integer."
        echo "Please set number of executions to an integer greater than 1. We recommend using at least 20."
        read -p "Number of simulation executions requested: " run_count
done
if ! [ ${comm_pattern} == "unstructured_mesh" ]; then
	x_procs=1
	y_procs=1
	z_procs=1
fi

# Confirm correctness of callstack tracing tool
while true; do
        case ${impl} in
                "glibc" | "libunwind" ) break ;;
                * ) echo "The selected tool for backtracing MPI functions is not supported by CSMPI at this time."
                        read -p "Please select one of the listed options for backtracing functions (glibc, libunwind). Input is case sensitive. " impl ;;
        esac
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
    if [ ${comm_pattern} == "unstructured_mesh" ]; then
	    echo "Topological Non-determinism Percentage ${nd_topo}"
    fi
    #if [ ${scheduler} == "slurm" ]; then
    echo "Queue for Running Scheduled Jobs: ${queue}"
    echo "Time Limit for Running Scheduled Jobs: ${time_limit}"
    #fi
    #if [ ${scheduler} == "lsf" ]; then
    #    echo "Queue for Running through LSF: ${lsf_queue}"
    #    echo "Time Limit for Running through LSF: ${lsf_time_limit}"
    #fi
    echo "Number of Execution Runs: ${run_count}"
    if [ ${comm_pattern} == "unstructured_mesh" ]; then
        echo "Unstructured Mesh Coordinates x*y*z = ${x_procs}*${y_procs}*${z_procs}"
    fi
    echo "Output will be stored in ${results_path}"
fi




# Define Needed Paths
cd anacin-x/config
example_paths_dir=$(pwd)
cd ${project_path}
source ${example_paths_dir}/anacin_paths.config
#config_path=${anacin_x_root}/apps/comm_pattern_generator/config
config_path=${results_path}/
comm_pattern_path=${anacin_x_root}/benchmark_analysis/benchmark_job_manager.sh


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
if [ ${comm_pattern} == "unstructured_mesh" ]; then
	echo "Topological Non-determinism Percentage: ${nd_topo}" >> ${user_config_file}
fi
#if [ ${scheduler} == "slurm" ]; then
    echo "Queue for Running Scheduled Jobs: ${queue}" >> ${user_config_file}
    echo "Time Limit for Running Scheduled Jobs: ${time_limit}" >> ${user_config_file}
#fi
#if [ ${scheduler} == "lsf" ]; then
#    echo "Queue for Running through LSF: ${lsf_queue}" >> ${user_config_file}
#    echo "Time Limit for Running through LSF: ${lsf_time_limit}" >> ${user_config_file}
#fi
echo "Number of Execution Runs: ${run_count}" >> ${user_config_file}
if [ ${comm_pattern} == "unstructured_mesh" ]; then
    echo "Unstructured Mesh Coordinates x*y*z = ${x_procs}*${y_procs}*${z_procs}" >> ${user_config_file}
fi
echo "Output will be stored in ${results_path}" >> ${user_config_file}


# Run Comm Pattern Script
bash ${comm_pattern_path} ${n_procs} ${n_iters} ${msg_sizes} ${n_nodes} ${queue} ${time_limit} 0 $((run_count-1)) ${results_path} ${example_paths_dir} ${x_procs} ${y_procs} ${z_procs} ${nd_start} ${nd_iter} ${nd_end} ${nd_topo} ${impl} ${comm_pattern} ${scheduler}
if [ ${comm_pattern} == "unstructured_mesh" ]; then
	echo "Your kernel distance data will be stored in output file: ${results_path}/msg_size_${msg_sizes}/n_procs_${n_procs}/n_iters_${n_iters}/ndp_${nd_start}_${nd_iter}_${nd_end}/nd_topological_${nd_topo}/kdts.pkl"
else
	echo "Your kernel distance data will be stored in output file: ${results_path}/msg_size_${msg_sizes}/n_procs_${n_procs}/n_iters_${n_iters}/ndp_${nd_start}_${nd_iter}_${nd_end}/kdts.pkl"
fi


# Communicate where to find visualization files
echo "Used the communication pattern type:                     ${comm_pattern}"
echo "Used graph kernel JSON file:                             ${graph_kernel}"
echo "Starting non-determinism percentage:                     ${nd_start}"
echo "Non-determinism percentage step size:                    ${nd_iter}"
echo "Ending non-determinism percentage:                       ${nd_end}"
if [ ${comm_pattern} == "unstructured_mesh" ]; then
	echo "Topological non-determinism percentage:                  ${nd_topo}"
fi


