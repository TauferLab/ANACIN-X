#!/usr/bin/env bash

n_procs=$1
run_idx_low=$2
run_idx_high=$3
results_root=$4

source ./example_paths_lsf.config

##message_sizes=(1 2 4 8 16 32 64 128 256 512 1024 2048)
##message_sizes=(1 512 1024 2048)
message_sizes=(512 1024 2048)

# Non-NINJA Workflow
for msg_size in ${message_sizes[@]};
do
    for run_idx in `seq -f "%03g" ${run_idx_low} ${run_idx_high}`; 
    do
        # Trace execution
        run_dir=${results_root}/msg_size_${msg_size}/without_ninja/run_${run_idx}/
        mkdir -p ${run_dir}
        app_config=${anacin_x_root}/apps/comm_pattern_generator/config/amg2013_msg_size_${msg_size}.json
        LD_PRELOAD=${pnmpi} PNMPI_LIB_PATH=${pnmpi_lib_path} PNMPI_CONF=${pnmpi_conf} mpirun -np ${n_procs} ${app_bin} ${app_config}
        mv dumpi-* ${run_dir}
        # Build event graph
        mpirun -np ${n_procs} ${dumpi_to_graph_bin} ${dumpi_to_graph_config} ${run_dir}
        event_graph=${run_dir}/event_graph.graphml
        # Extract slices
        mpirun -np 10 ${extract_slices_script} ${event_graph} ${slicing_policy} -o "slices"
    done
    mpirun -np 10 ${compute_kdts_script} "${results_root}/msg_size_${msg_size}/without_ninja/" ${graph_kernel} --slice_dir_name "slices" -o "kdts.pkl"
done

