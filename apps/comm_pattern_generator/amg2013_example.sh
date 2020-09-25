#!/usr/bin/env bash

n_procs=$1
run_idx_low=$2
run_idx_high=$3

source $HOME/Src_ANACIN-X/apps/comm_pattern_generator/example_paths.config

#anacin_x_root=$HOME/Src_ANACIN-X
#
## Tracing
#pnmpi=${anacin_x_root}/submodules/PnMPI/build/lib/libpnmpi.so
#pnmpi_lib_path=${anacin_x_root}/anacin-x/job_scripts/pnmpi_patched_libs/
#app_bin=${anacin_x_root}/apps/comm_pattern_generator/build/comm_pattern_generator
#
## Event graph construction
#dumpi_to_graph_bin=${anacin_x_root}/submodules/dumpi_to_graph/build/dumpi_to_graph
#dumpi_to_graph_config=${anacin_x_root}/submodules/dumpi_to_graph/config/dumpi_only.json
#
## Slice extraction
#extract_slices_script=${anacin_x_root}/anacin-x/event_graph_analysis/extract_slices.py
#slicing_policy=${anacin_x_root}/anacin-x/event_graph_analysis/slicing_policies/barrier_delimited_full.json
#
## Kernel distance time series computation
#compute_kdts_script=${anacin_x_root}/anacin-x/event_graph_analysis/compute_kernel_distance_time_series.py
#graph_kernel=${anacin_x_root}/anacin-x/event_graph_analysis/graph_kernel_policies/wlst_5iters_logical_timestamp_label.json
#
##message_sizes=(1 2 4 8 16 32 64 128 256 512 1024 2048)
##message_sizes=(1 512 1024 2048)
message_sizes=(2048)

results_root=/data/gclab/anacin-n/anacin_results

# Non-NINJA Workflow
for msg_size in ${message_sizes[@]};
do
    for run_idx in `seq -f "%03g" ${run_idx_low} ${run_idx_high}`; 
    do
        # Trace execution
        run_dir=${results_root}/msg_size_${msg_size}/without_ninja/run_${run_idx}/
        mkdir -p ${run_dir}
#        pnmpi_conf=${anacin_x_root}/anacin-x/job_scripts/pnmpi_configs/dumpi.conf
	pnmpi_conf=${anacin_x_root}/anacin-x/pnmpi/configs/dumpi.conf
        app_config=${anacin_x_root}/apps/comm_pattern_generator/config/amg2013_example_msg_size_${msg_size}.json
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

