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
build_graph_job=${anacin_x_root}/anacin-x/tracing/mini_amr/example_problems/2_moving_spheres_16_procs/build_graph.sh
squash_barriers_job=${ega_root}/squash_barriers.py

# Locations of dumpi_to_graph stuff
dumpi_to_graph_bin=${anacin_x_root}/submodules/dumpi_to_graph/build/dumpi_to_graph
dumpi_to_graph_config=${anacin_x_root}/submodules/dumpi_to_graph/config/with_callstacks.json

export pnmpi
export pnmpi_lib_path
export pnmpi_conf

# Execute the workflow
for run_idx in `seq -f "%04g" ${run_idx_low} ${run_idx_high}`;
do
    # Construct the event graph for this run
    build_graph_stdout=$( sbatch -N1 ${build_graph_job} ${run_dir} ${dumpi_to_graph_bin} ${dumpi_to_graph_config} )
    build_graph_job_id=$( echo ${build_graph_job_stdout} | sed 's/[^0-9]*//g' )

    # Merge consecutive barrier nodes together in event graph
    event_graph=${run_dir}/event_graph.graphml
    squash_barriers_stdout=$( sbatch -N1 --dependency:afterok=${build_graph_job_id} ${squash_barriers_job} ${event_graph} )
    squash_barriers_job_id=$( echo ${squash_barriers_stdout} | sed 's/[^0-9]*//g' )
done
