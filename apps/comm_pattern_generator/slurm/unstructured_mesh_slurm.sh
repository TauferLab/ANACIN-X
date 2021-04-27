#!/usr/bin/env bash

n_procs=$1
n_iters=$2
msg_size=$3
n_nodes=$4
slurm_queue=$5
slurm_time_limit=$6
run_idx_low=$7
run_idx_high=$8
results_root=$9
example_paths_dir=${10}
x_procs=${11}
y_procs=${12}
z_procs=${13}

source ${example_paths_dir}/example_paths_slurm.config
#example_paths_dir=$(pwd)
#echo ${example_paths_dir}
#echo ${anacin_x_root}

function join_by { local IFS="$1"; shift; echo "$*"; }

proc_placement=("pack")
nd_neighbor_fractions=("0" "0.25" "0.5" "0.75" "1")
comm_pattern_run_script=${anacin_x_root}/apps/comm_pattern_generator/slurm/unstructured_mesh_run.sh
n_procs_per_node=$((n_procs/n_nodes))

queue=${slurm_queue}
time_limit=${slurm_time_limit}

for proc_placement in ${proc_placement[@]};
do
    for nd_neighbor_fraction in ${nd_neighbor_fractions[@]};
    do
    #echo "Launching jobs for: proc. placement = ${proc_placement}, # procs. = ${n_procs}, msg. size = ${msg_size}"
    
    runs_root=${results_root}/msg_size_${msg_size}/n_procs_${n_procs}/n_iters_${n_iters}/proc_placement_${proc_placement}/nd_neighbor_fraction_${nd_neighbor_fraction}/
    
    # Launch intra-execution jobs
    kdts_job_deps=()
    for run_idx in `seq -f "%03g" ${run_idx_low} ${run_idx_high}`; 
    do
        echo "Launching run ${run_idx} for: proc. placement = ${proc_placement}, # procs. = ${n_procs}, msg. size = ${msg_size}, nd. neighbor fraction = ${nd_neighbor_fraction}"

        # Set up results dir
        run_dir=${runs_root}/run_${run_idx}/
        mkdir -p ${run_dir}
	
        comm_pattern_run_name=unstructured_mesh_run_$(date +%s.%N)
        comm_pattern_run_stdout=$( sbatch -N ${n_nodes} -p ${queue} -J ${comm_pattern_run_name} -t ${time_limit} -n ${n_procs} --ntasks-per-node=${n_procs_per_node} ${comm_pattern_run_script} ${n_procs} ${msg_size} ${n_iters} ${proc_placement} ${nd_neighbor_fraction} ${run_dir} ${example_paths_dir} ${debug_dir} ${x_procs} ${y_procs} ${z_procs} )
        while [ -z "$comm_pattern_run_id" ]; do
            #echo "Waiting for jobid"
            #comm_pattern_run_stdout=$( sbatch -N ${n_nodes} -p ${queue} -J ${comm_pattern_run_name} -t ${time_limit} -n ${n_procs} --ntasks-per-node=${n_procs_per_node} ${comm_pattern_run_script} ${n_procs} ${msg_size} ${n_iters} ${proc_placement} ${nd_neighbor_fraction} ${run_dir} ${example_paths_dir} ${debug_dir} )
            comm_pattern_run_id=$( sacct -n -X --format jobid --name ${comm_pattern_run_name} )
        done
        kdts_job_deps+=${comm_pattern_run_id}
        comm_pattern_run_id=""
	
    done # runs
    
    # Compute kernel distances for each slice
    kdts_job_dep_str=$( join_by : ${kdts_job_deps[@]} )
    cd ${runs_root}
    compute_kdts_stdout=$( sbatch -N ${n_nodes} -p ${queue} -t ${time_limit} -n ${n_procs} --ntasks-per-node=${n_procs_per_node} -o compute_kdts_out.txt -e compute_kdts_err.txt --dependency=afterok:${kdts_job_dep_str} ${job_script_compute_kdts} ${n_procs} ${compute_kdts_script} ${runs_root} ${graph_kernel} )
    compute_kdts_job_id=$( echo ${compute_kdts_stdout} | sed 's/[^0-9]*//g' )
    
    done
done # proc placement
