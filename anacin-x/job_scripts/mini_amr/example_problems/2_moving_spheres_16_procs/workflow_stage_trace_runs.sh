#!/usr/bin/env bash

source ../../../../base_vars.sh

# Top level directory for holding results
root_dir=$1

# Number of runs to do
run_idx_low=$2
run_idx_high=$3

# Multi-node or single node runs?
multi_node_runs=$4

# miniAMR executable location
mini_amr_bin=${anacin_x_root}/apps/miniAMR/ref/ma.x

# miniAMR parameters
load_balancing_policy=$5
load_balancing_threshold=$6
refinement_policy=$7
refinement_frequency=$8

# Create a directory to hold all of the results from these runs, and any data
# derived from cross-run analysis (e.g., kernel distance time series)
results_dir="${root_dir}/2_moving_spheres_16_procs/multi_node_runs/"
mkdir -p ${results_dir}

# Locations of job scripts invoked in this workflow
if [ ${multi_node_runs} -eq 1 ]
then
    trace_job=${anacin_x_root}/anacin-x/tracing/mini_amr/example_problems/2_moving_spheres_16_procs/trace_multi_node.sh
    n_nodes_tracing=16
else:
    trace_job=${anacin_x_root}/anacin-x/tracing/mini_amr/example_problems/2_moving_spheres_16_procs/trace_single_node.sh
    n_nodes_tracing=1
fi

# Locations of PnMPI stuff for composing the various tracing modules 
pnmpi=${anacin_x_root}/submodules/PnMPI/build/lib/libpnmpi.so
pnmpi_lib_path=${anacin_x_root}/anacin-x/tracing/pnmpi_patched_libs/
pnmpi_conf=${anacin_x_root}/anacin-x/tracing/pnmpi_configs/dumpi_and_csmpi.conf

export pnmpi
export pnmpi_lib_path
export pnmpi_conf

# Execute the workflow
for run_idx in `seq -f "%04g" ${run_idx_low} ${run_idx_high}`;
do
    # Make the directory that will hold this run's trace files, event graph, 
    # and any other derived data (e.g., event graph slices) 
    run_dir=${results_dir}/run_${run_idx}/
    mkdir -p ${run_dir}
    cd ${run_dir}

    # Trace the application
    sbatch -N${n_nodes_tracing} ${trace_job} ${mini_amr_bin} ${load_balancing_policy} ${load_balancing_threshold} ${refinement_policy} ${refinement_frequency}
done
