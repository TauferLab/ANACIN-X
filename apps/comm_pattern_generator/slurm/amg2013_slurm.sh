#!/usr/bin/env bash

n_procs=$1
n_iters=$2
msg_size=$3
slurm_queue=$4
slurm_time_limit=$5
run_idx_low=$6
run_idx_high=$7
results_root=$8


source ./example_paths_slurm.config
example_paths_dir=$(pwd)
#echo ${example_paths_dir}
#echo ${anacin_x_root}

function join_by { local IFS="$1"; shift; echo "$*"; }

proc_placement=("pack")
comm_pattern_run_script=${anacin_x_root}/apps/comm_pattern_generator/slurm/amg2013_run.sh

queue=${slurm_queue}
time_limit=${slurm_time_limit}

for proc_placement in ${proc_placement[@]};
do
    echo "Launching jobs for: proc. placement = ${proc_placement}, # procs. = ${n_procs}, msg. size = ${msg_size}"
    
    runs_root=${results_root}/n_procs_${n_procs}/proc_placement_${proc_placement}/msg_size_${msg_size}/
    
    # Launch intra-execution jobs
    kdts_job_deps=()
    for run_idx in `seq -f "%03g" ${run_idx_low} ${run_idx_high}`; 
    do
        # Set up results dir
        run_dir=${runs_root}/run_${run_idx}/
        mkdir -p ${run_dir}
	
        comm_pattern_run_name=amg2013_run_$(date +%s.%N)
        comm_pattern_run_stdout=$( sbatch -N 1 -p ${queue} -J ${comm_pattern_run_name} -t ${time_limit} -n ${n_procs} ${comm_pattern_run_script} ${n_procs} ${msg_size} ${n_iters} ${proc_placement} ${run_dir} ${example_paths_dir} )
        while [ -z "$comm_pattern_run_id" ]; do
            comm_pattern_run_id=$( sacct -n -X --format jobid --name ${comm_pattern_run_name} )
        done
        kdts_job_deps+=${comm_pattern_run_id}
        comm_pattern_run_id=""
	
    done # runs
    
    # Compute kernel distances for each slice
    kdts_job_dep_str=$( join_by : ${kdts_job_deps[@]} )
    cd ${runs_root}
    compute_kdts_stdout=$( sbatch -N 1 -p ${queue} -t ${time_limit} -n ${n_procs} -o compute_kdts_out.txt -e compute_kdts_err.txt --dependency=afterok:${kdts_job_dep_str} ${job_script_compute_kdts} ${n_procs} ${compute_kdts_script} ${runs_root} ${graph_kernel} )
    compute_kdts_job_id=$( echo ${compute_kdts_stdout} | sed 's/[^0-9]*//g' )
    
done # proc placement
