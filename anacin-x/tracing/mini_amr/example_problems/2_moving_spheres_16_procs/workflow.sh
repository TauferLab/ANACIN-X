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

# Event graph slicing policy
slicing_policy=$9

# Graph kernel parameters
graph_kernels=${10}

# Anomaly detection policy
anomaly_detection_policy=${11}

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
build_graph_job=${anacin_x_root}/anacin-x/tracing/mini_amr/example_problems/2_moving_spheres_16_procs/build_graph.sh
squash_barriers_job=${ega_root}/squash_barriers.py
extract_slices_job=${ega_root}/extract_slices.py
compute_kdts_job=${ega_root}/compute_kernel_distance_time_series.py
anomaly_detection_job=${ega_root}/anomaly_detection.py
callstack_analysis_job=${ega_root}/callstack_analysis.py
visualize_kdts_job=${ega_root}/visualization/visualize_kernel_distance_time_series.py
visualize_callstack_report_job=${ega_root}/visualization/visualize_callstack_report.py

# Locations of PnMPI stuff for composing the various tracing modules 
pnmpi=${anacin_x_root}/submodules/PnMPI/build/lib/libpnmpi.so
pnmpi_lib_path=${anacin_x_root}/anacin-x/tracing/pnmpi_patched_libs/
pnmpi_conf=${anacin_x_root}/anacin-x/tracing/pnmpi_configs/dumpi_and_csmpi.conf

# Locations of dumpi_to_graph stuff
dumpi_to_graph_bin=${anacin_x_root}/submodules/dumpi_to_graph/build/dumpi_to_graph
dumpi_to_graph_config=${anacin_x_root}/submodules/dumpi_to_graph/config/with_callstacks.json


export pnmpi
export pnmpi_lib_path
export pnmpi_conf

# Convenience function for making the dependency lists for the kernel distance
# time series job
function join_by { local IFS="$1"; shift; echo "$*"; }

# Array to store all extract slices job IDs so that the kernel distance time 
# series job does not start until all of the extract slices jobs are done
compute_kdts_job_dependencies=()

# Execute the workflow
for run_idx in `seq -f "%04g" ${run_idx_low} ${run_idx_high}`;
do
    # Make the directory that will hold this run's trace files, event graph, 
    # and any other derived data (e.g., event graph slices) 
    run_dir=${results_dir}/run_${run_idx}/
    mkdir -p ${run_dir}
    cd ${run_dir}

    # Trace the application
    trace_job_stdout=$( sbatch -N${n_nodes_tracing} ${trace_job} ${mini_amr_bin} ${load_balancing_policy} ${load_balancing_threshold} ${refinement_policy} ${refinement_frequency} )
    trace_job_id=$( echo ${trace_job_stdout} | sed 's/[^0-9]*//g' )

    # Construct the event graph for this run
    build_graph_stdout=$( sbatch -N1 --dependency:afterok=${trace_job_id} ${build_graph_job} ${run_dir} ${dumpi_to_graph_bin} ${dumpi_to_graph_config} )
    build_graph_job_id=$( echo ${build_graph_job_stdout} | sed 's/[^0-9]*//g' )

    # Merge consecutive barrier nodes together in event graph
    event_graph=${run_dir}/event_graph.graphml
    squash_barriers_stdout=$( sbatch -N1 --dependency:afterok=${build_graph_job_id} ${squash_barriers_job} ${event_graph} )
    squash_barriers_job_id=$( echo ${squash_barriers_stdout} | sed 's/[^0-9]*//g' )

    # Extract slices
    event_graph=${run_dir}/event_graph_squashed.graphml
    extract_slices_stdout=$( sbatch -N1 --dependency:afterok=${squash_barriers_job_id} ${extract_slices_job} ${event_graph} ${slicing_policy} )
    extract_slices_job_id=$( echo ${extract_slices_stdout} | sed 's/[^0-9]*//g' )
    compute_kdts_job_dependencies+=${extract_slices_job_id}
done

# Compute the kernel distance time series
all_extract_slices_job_ids=$( join_by : "${compute_kdts_job_dependencies[@]}" )
compute_kdts_stdout=$( sbatch -N1 --dependency:afterok=${all_extract_slices_job_ids} ${compute_kdts_job} ${results_dir} ${slicing_policy} ${graph_kernels} --callstacks_available )
compute_kdts_job_id=$( echo ${compute_kdts_stdout} | sed 's/[^0-9]*//g' )

# Perform anomaly detection on the resulting time series of kernel distance distributions
kdts_data=${results_dir}/kdts.pkl
anomaly_detection_stdout=$( sbatch -N1 --dependency:afterok=${compute_kdts_job_id} ${anomaly_detection_job} ${kdts_data} ${anomaly_detection_policy} )
anomaly_detection_job_id=$( echo ${anomaly_detection_stdout} | sed 's/[^0-9]*//g' )

# Analyze the callstack distribution obtained from anomaly detection 
anomaly_data=${results_dir}/anomalies.pkl
callstack_analysis_stdout=$( sbatch -N1 --dependency:afterok=${anomaly_detection_job_id} ${callstack_analysis_job} ${anomaly_data} ${mini_amr_bin} )
callstack_analysis_job_id=$( echo ${callstack_analysis_stdout} | sed 's/[^0-9]*//g' )

# Make kernel distance time series visualizations
sbatch -N1 --dependency:afterok=${compute_kdts_job_id} ${visualize_kdts_job} ${kdts_data}

# Make callstack analysis visualizations
callstack_report=${results_dir}/callstack_report.json
sbatch -N1 --dependency:afterok${callstack_analysis_job_id} ${visualizae_callstack_report_job} ${callstack_report}
