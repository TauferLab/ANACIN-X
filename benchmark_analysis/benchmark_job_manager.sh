#!/usr/bin/env bash

n_procs=$1
n_iters=$2
msg_size=$3
n_nodes=$4
queue=$5
time_limit=$6
run_idx_low=$7
run_idx_high=$8
results_root=$9
paths_dir=${10}
x_procs=${11}
y_procs=${12}
z_procs=${13}
nd_start=${14}
nd_iter=${15}
nd_end=${16}
nd_neighbor_fraction=${17}
impl=${18}
#run_csmpi=${19}
comm_pattern=${19}
scheduler=${20}
in_option=${21}

source ${paths_dir}/anacin_paths.config

if [ "${scheduler}" == "slurm" ]; then
	function join_by { local IFS="$1"; shift; echo "$*"; }
fi
if [ "${scheduler}" == "lsf" ]; then
	function join_by { local d=$1; shift; local f=$1; shift; printf %s "$f" "${@/#/$d}"; }
fi

proc_placement=("pack")
comm_pattern_run_script=${anacin_x_root}/benchmark_analysis/benchmark_run_manager.sh
procs_per_node=$(echo "scale=2; $n_procs/$n_nodes" |bc -l)
if [[ "$procs_per_node" =~ ^[0-9]+[.][0][0]$ ]]; then
	n_procs_per_node=$((n_procs/n_nodes))
else
	n_procs_per_node=$((n_procs/n_nodes+1))
fi

if [ "${comm_pattern}" == "unstructured_mesh" ]; then
	runs_root=${results_root}/msg_size_${msg_size}/n_procs_${n_procs}/n_iters_${n_iters}/ndp_${nd_start}_${nd_iter}_${nd_end}/nd_topological_${nd_neighbor_fraction}/
else
	runs_root=${results_root}/msg_size_${msg_size}/n_procs_${n_procs}/n_iters_${n_iters}/ndp_${nd_start}_${nd_iter}_${nd_end}/
fi

kdts_job_deps=()
for run_idx in `seq -f "%03g" ${run_idx_low} ${run_idx_high}`; do
	
	echo "Submitting jobs for run ${run_idx} of the ${comm_pattern} communication pattern on scheduler=${scheduler}"
	run_dir=${runs_root}/run_${run_idx}/
        mkdir -p ${run_dir}
	debugging_path=${run_dir}/debug
	mkdir -p ${debugging_path}
	cd ${run_dir}

	comm_pattern_run_name=${comm_pattern}_run_$(date +%s.%N)
	
	if [ "${scheduler}" == "slurm" ]; then
		comm_pattern_run_stdout=$( sbatch -N ${n_nodes} -p ${queue} -J ${comm_pattern_run_name} -t ${time_limit} -n ${n_procs} --ntasks-per-node=${n_procs_per_node} ${comm_pattern_run_script} ${n_procs} ${msg_size} ${n_iters} ${proc_placement} ${run_idx} ${run_dir} ${paths_dir} ${nd_start} ${nd_iter} ${nd_end} ${impl} ${comm_pattern} ${nd_neighbor_fraction} ${x_procs} ${y_procs} ${z_procs} ${in_option})
		comm_pattern_run_id=$( echo ${comm_pattern_run_stdout} | sed 's/[^0-9]*//g' )" "
		kdts_job_deps+=${comm_pattern_run_id}
        comm_pattern_run_id=""
	fi

	if [ "${scheduler}" == "lsf" ]; then
		comm_pattern_run_stdout=$( bsub -n ${n_procs} -R "span[ptile=${n_procs_per_node}]" -q ${queue} -W ${time_limit} -o ${debugging_path}/lsf_output.txt -e ${debugging_path}/lsf_error.txt ${comm_pattern_run_script} ${n_procs} ${msg_size} ${n_iters} ${proc_placement} ${run_idx} ${run_dir} ${paths_dir} ${nd_start} ${nd_iter} ${nd_end} ${impl} ${comm_pattern} ${nd_neighbor_fraction} ${x_procs} ${y_procs} ${z_procs} ${in_option})
		comm_pattern_job_id=$( echo ${comm_pattern_run_stdout} | sed 's/[^0-9]*//g' )
		kdts_job_deps+=("done(${comm_pattern_job_id})")
	fi
	
	if [ "${scheduler}" == "unscheduled" ]; then
		bash ${comm_pattern_run_script} ${n_procs} ${msg_size} ${n_iters} ${proc_placement} ${run_idx} ${run_dir} ${paths_dir} ${nd_start} ${nd_iter} ${nd_end} ${impl} ${comm_pattern} ${nd_neighbor_fraction} ${x_procs} ${y_procs} ${z_procs} ${in_option}
	fi


done

cd ${runs_root}
echo "Submitting job to compute KDTS data for ${comm_pattern} communication pattern with $((run_idx_high+1)) runs on scheduler=${scheduler}"

if [ "${scheduler}" == "slurm" ]; then
	kdts_job_dep_str=$( join_by : ${kdts_job_deps[@]} )
	compute_kdts_stdout=$( sbatch -N ${n_nodes} -p ${queue} -t ${time_limit} -n ${n_procs} --ntasks-per-node=${n_procs_per_node} -o ${debugging_path}/../../compute_kdts_out.txt -e ${debugging_path}/../../compute_kdts_err.txt --dependency=afterok:${kdts_job_dep_str} ${job_script_compute_kdts} ${n_procs_compute_kdts} ${compute_kdts_script} ${runs_root} ${graph_kernel} ${slicing_policy} ${paths_dir} )
	compute_kdts_job_id=$( echo ${compute_kdts_stdout} | sed 's/[^0-9]*//g' )
fi

if [ "${scheduler}" == "lsf" ]; then
	kdts_job_dep_str=$( join_by "&&" ${kdts_job_deps[@]} )
	compute_kdts_stdout=$(bsub -n ${n_procs} -R "span[ptile=${n_procs_per_node}]" -w ${kdts_job_dep_str} -o ${debugging_path}/../../compute_kdts_output.txt -e ${debugging_path}/../../compute_kdts_error.txt -q ${queue} -W ${time_limit} ${job_script_compute_kdts} ${n_procs_compute_kdts} ${compute_kdts_script} ${runs_root} ${graph_kernel} ${slicing_policy} ${paths_dir} )
	compute_kdts_job_id=$( echo ${compute_kdts_stdout} | sed 's/[^0-9]*//g' )
fi

if [ "${scheduler}" == "unscheduled" ]; then
	bash > ${debugging_path}/../../compute_kdts_output.txt 2> ${debugging_path}/../../compute_kdts_error.txt ${job_script_compute_kdts} ${n_procs_compute_kdts} ${compute_kdts_script} ${runs_root} ${graph_kernel} ${slicing_policy} ${paths_dir}
fi






