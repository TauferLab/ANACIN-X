#!/bin/bash

n_procs=$1
msg_size=$2
n_iters=$3
proc_placement=$4
run_idx=$5
run_dir=$6
paths_dir=$7
nd_start=$8
nd_iter=$9
nd_end=${10}
impl=${11}
#run_csmpi=${12}
comm_pattern=${12}
nd_neighbor_fraction=${13}
x_procs=${14}
y_procs=${15}
z_procs=${16}
run_root="$run_dir""../../../../"


source ${paths_dir}/anacin_paths.config

cd ${run_dir}
debugging_path=${run_dir}/debug
mkdir -p ${debugging_path}

if [ "${run_csmpi}" == "True" ]; then
	#Set up csmpi configuration
	trace_dir=${run_dir}
	default_config="default_config_${impl}_run_${run_idx}.json"
	mkdir -p ${trace_dir}
	python3 ${csmpi_conf}/generate_config.py -o ${run_dir}/${default_config} --backtrace_impl ${impl} -d ${trace_dir}
	export CSMPI_CONFIG=${run_dir}/${default_config}
fi


# Create app config if doesn't exist
proc_grid="${x_procs}x${y_procs}x${z_procs}"
if [ "${comm_pattern}" == "unstructured_mesh" ]; then
	#app_config=${anacin_x_root}/apps/comm_pattern_generator/config/unstructured_mesh_${proc_grid}_nd_neighbor_fraction_${nd_neighbor_fraction}_msg_size_${msg_size}_niters_${n_iters}_ndp_${nd_start}_${nd_iter}_${nd_end}.json
	app_config=${run_root}/unstructured_mesh_${proc_grid}_nd_neighbor_fraction_${nd_neighbor_fraction}_msg_size_${msg_size}_niters_${n_iters}_ndp_${nd_start}_${nd_iter}_${nd_end}.json
fi
if [ "${comm_pattern}" == "amg2013" ]; then
	#app_config=${anacin_x_root}/apps/comm_pattern_generator/config/amg2013_msg_size_${msg_size}_niters_${n_iters}_ndp_${nd_start}_${nd_iter}_${nd_end}.json
	app_config=${run_root}/amg2013_msg_size_${msg_size}_niters_${n_iters}_ndp_${nd_start}_${nd_iter}_${nd_end}.json
fi
if [ "${comm_pattern}" == "message_race" ]; then
    #app_config=${anacin_x_root}/apps/comm_pattern_generator/config/message_race_msg_size_${msg_size}_niters_${n_iters}_ndp_${nd_start}_${nd_iter}_${nd_end}.json
    app_config=${run_root}/message_race_msg_size_${msg_size}_niters_${n_iters}_ndp_${nd_start}_${nd_iter}_${nd_end}.json
fi
if [ ! -f "$app_config" ]; then
	if [ "${comm_pattern}" == "unstructured_mesh" ]; then
		#python3 > ${debugging_path}/create_json_output.txt 2> ${debugging_path}/create_json_error.txt ${anacin_x_root}/apps/comm_pattern_generator/config/json_gen.py "unstructured_mesh" ${nd_neighbor_fraction} ${x_procs} ${y_procs} ${z_procs} ${msg_size} ${n_iters} "${anacin_x_root}/apps/comm_pattern_generator/" ${nd_start} ${nd_iter} ${nd_end}
		python3 > ${debugging_path}/create_json_output.txt 2> ${debugging_path}/create_json_error.txt ${anacin_x_root}/apps/comm_pattern_generator/config/json_gen.py "unstructured_mesh" ${nd_neighbor_fraction} ${x_procs} ${y_procs} ${z_procs} ${msg_size} ${n_iters} "${run_root}/" ${nd_start} ${nd_iter} ${nd_end}
	fi
	if [ "${comm_pattern}" == "amg2013" ]; then
		#python3 > ${debugging_path}/create_json_output.txt 2> ${debugging_path}/create_json_error.txt ${anacin_x_root}/apps/comm_pattern_generator/config/json_gen.py "amg2013" ${msg_size} ${n_iters} "${anacin_x_root}/apps/comm_pattern_generator/" ${nd_start} ${nd_iter} ${nd_end}
		python3 > ${debugging_path}/create_json_output.txt 2> ${debugging_path}/create_json_error.txt ${anacin_x_root}/apps/comm_pattern_generator/config/json_gen.py "amg2013" ${msg_size} ${n_iters} "${run_root}/" ${nd_start} ${nd_iter} ${nd_end}
	fi
	if [ "${comm_pattern}" == "message_race" ]; then
        #python3 > ${debugging_path}/create_json_output.txt 2> ${debugging_path}/create_json_error.txt ${anacin_x_root}/apps/comm_pattern_generator/config/json_gen.py "naive_reduce" ${msg_size} ${n_iters} "${anacin_x_root}/apps/comm_pattern_generator/" ${nd_start} ${nd_iter} ${nd_end}
        python3 > ${debugging_path}/create_json_output.txt 2> ${debugging_path}/create_json_error.txt ${anacin_x_root}/apps/comm_pattern_generator/config/json_gen.py "naive_reduce" ${msg_size} ${n_iters} "${run_root}/" ${nd_start} ${nd_iter} ${nd_end}
	fi
fi


# Trace execution
bash > ${debugging_path}/trace_exec_output.txt 2> ${debugging_path}/trace_exec_error.txt ${job_script_trace_pack_procs} ${n_procs} ${app_bin} ${app_config} ${paths_dir}

# Build event graph
bash > ${debugging_path}/build_graph_output.txt 2> ${debugging_path}/build_graph_error.txt ${job_script_build_graph} ${n_procs} ${dumpi_to_graph_bin} ${dumpi_to_graph_config} ${run_dir}
event_graph=${run_dir}/event_graph.graphml

# Extract slices
bash > ${debugging_path}/extract_slices_output.txt 2> ${debugging_path}/extract_slices_error.txt ${job_script_extract_slices} ${n_procs_extract_slices} ${extract_slices_script} ${event_graph} ${slicing_policy}

