#!/bin/bash

n_procs=$1
msg_size=$2
n_iters=$3
proc_placement=$4
nd_neighbor_fraction=$5
run_dir=$6
example_paths_dir=$7
debug_dir=$8

source ${example_paths_dir}/example_paths_slurm.config

cd ${run_dir}
debug_dir=${run_dir}/debug
mkdir -p ${debug_dir}

# Create app config if doesn't exist
proc_grid="4x3x2"
app_config=${anacin_x_root}/apps/comm_pattern_generator/config/unstructured_mesh_${proc_grid}_nd_neighbor_fraction_${nd_neighbor_fraction}_msg_size_${msg_size}_niters_${n_iters}.json
if [ ! -f "$app_config" ]; then
    python3 > ${debug_dir}/create_json_output.txt 2> ${debug_dir}/create_json_error.txt ${anacin_x_root}/apps/comm_pattern_generator/config/json_gen.py "unstructured_mesh" ${nd_neighbor_fraction} 4 3 2 ${msg_size} ${n_iters} "${example_paths_dir}/../"
fi

echo ${app_config}
# Trace execution
LD_PRELOAD=${pnmpi} PNMPI_LIB_PATH=${pnmpi_lib_path} PNMPI_CONF=${pnmpi_conf} mpirun -np ${n_procs} > ${debug_dir}/trace_exec_output.txt 2> ${debug_dir}/trace_exec_error.txt ${app_bin} ${app_config}
mv dumpi-* ${run_dir}

# Build event graph
mpirun -np ${n_procs} > ${debug_dir}/build_graph_output.txt 2> ${debug_dir}/build_graph_error.txt ${dumpi_to_graph_bin} ${dumpi_to_graph_config} ${run_dir}
event_graph=${run_dir}/event_graph.graphml

# Extract slices
mpirun -np ${n_procs} > ${debug_dir}/extract_slices_output.txt 2> ${debug_dir}/extract_slices_error.txt ${extract_slices_script} ${event_graph} ${slicing_policy} -o "slices"

