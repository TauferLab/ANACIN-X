#!/usr/bin/env bash                                                                                                                         

n_procs=$1
n_iters=$2
msg_size=$3
n_nodes=$4
run_idx_low=$5
run_idx_high=$6
results_root=$7
example_paths_dir=$8

source ${example_paths_dir}/example_paths_lsf.config
#example_paths_dir=$(pwd)

function join_by { local d=$1; shift; local f=$1; shift; printf %s "$f" "${@/#/$d}"; }
kdts_job_deps=()

comm_pattern_job_script=${anacin_x_root}/apps/comm_pattern_generator/lsf/amg2013.sh
n_procs_per_node=$((n_procs/n_nodes))

for run_idx in `seq -f "%03g" ${run_idx_low} ${run_idx_high}`;
do

    # Set up paths
    run_dir=${results_root}/msg_size_${msg_size}/n_procs_${n_procs}/n_iters_${n_iters}/run_${run_idx}
    mkdir -p ${run_dir}
    debugging_path=${run_dir}/debug
    mkdir -p ${debugging_path}
    cd ${run_dir}

    #bsub -n ${n_procs} ${message_race_script} ${n_procs} ${n_iters} ${msg_size} ${run_idx_low} ${run_idx_high} ${results_root}
    comm_pattern_run_stdout=$( bsub -n ${n_procs} -R "span[ptile=${n_procs_per_node}]" -o ${debugging_path}/lsf_output.txt -e ${debugging_path}/lsf_error.txt ${comm_pattern_job_script} ${n_procs} ${n_iters} ${msg_size} ${n_nodes} ${run_idx} ${example_paths_dir} ${run_dir} )
    comm_pattern_job_id=$( echo ${comm_pattern_run_stdout} | sed 's/[^0-9]*//g' )
    kdts_job_deps+=("done(${comm_pattern_job_id})")
    echo ${kdts_job_deps} 

done

kdts_job_dep_str=$( join_by "&&" ${kdts_job_deps[@]} )
echo ${kdts_job_dep_str}
cd ${run_dir}/../
bsub -n ${n_procs} -R "span[ptile=${n_procs_per_node}]" -w ${kdts_job_dep_str} -o compute_kdts_output.txt -e compute_kdts_error.txt ${compute_kdts_script} "${run_dir}/../" ${graph_kernel} --slice_dir_name "slices" -o "kdts.pkl"



#amg2013_script=${anacin_x_root}/apps/comm_pattern_generator/lsf/amg2013.sh

#n_procs_per_node=$((n_procs/n_nodes))

#bsub -n ${n_procs} -R "span[ptile=${n_procs_per_node}]" -o ${debugging_path}/lsf_output.txt -e ${debugging_path}/lsf_error.txt ${amg2013_script} ${n_procs} ${n_iters} ${msg_size} ${n_nodes} ${run_idx_low} ${run_idx_high} ${results_root}
