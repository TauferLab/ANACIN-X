#!/usr/bin/env bash

source ../../../../../base_vars.sh

# Top level directory for holding results
root_dir=$1

# Number of runs to do
run_idx_low=$2
run_idx_high=$3

# Multi-node or single node runs?
multi_node_runs=$4

# Max number of processes that we'll run on a single node in this workflow
n_procs_per_node=32

# miniAMR executable location
mini_amr_bin=${anacin_x_root}/apps/miniAMR/ref/ma.x

# miniAMR parameters
load_balancing_policy=$5
load_balancing_threshold="$6"
refinement_policy=$7
refinement_frequency=$8

# Event graph slicing policy
#slicing_policy=$9
slicing_policy=${anacin_x_root}/anacin-x/event_graph_analysis/slicing_policies/barrier_delimited_full.json

## Graph kernel parameters
#graph_kernels=${10}
#
## Anomaly detection policy
#anomaly_detection_policy=${11}

# Create a directory to hold all of the results from these runs, and any data
# derived from cross-run analysis (e.g., kernel distance time series)
app_config="/lb_policy_${load_balancing_policy}_lb_thresh_${load_balancing_threshold}_ref_policy_${refinement_policy}_ref_freq_${refinement_frequency}/"
if [ ${multi_node_runs} -eq 1 ]
then
    results_dir="${root_dir}/2_moving_spheres_16_procs/multi_node_runs/${app_config}"
else
    results_dir="${root_dir}/2_moving_spheres_16_procs/single_node_runs/${app_config}"
fi
mkdir -p ${results_dir}

# Locations of job script and config file generation utilities
job_script_dir="${anacin_x_root}/anacin-x/job_scripts/mini_amr/example_problems/2_moving_spheres_16_procs/lsf/"
job_script_generator=${job_script_dir}/job_script_generator.py
csmpi_config_generator=${anacin_x_root}/submodules/csmpi/config/generate_config.py
csmpi_config_functions=${anacin_x_root}/submodules/csmpi/config/mpi_function_subsets/mini_amr.json


# Locations of PnMPI stuff for composing the various tracing modules 
pnmpi=${anacin_x_root}/submodules/PnMPI/build/lib/libpnmpi.so
pnmpi_lib_path=${anacin_x_root}/anacin-x/job_scripts/pnmpi_patched_libs/
pnmpi_conf=${anacin_x_root}/anacin-x/job_scripts/pnmpi_configs/dumpi_and_csmpi.conf

# Locations of dumpi_to_graph stuff
dumpi_to_graph_bin=${anacin_x_root}/submodules/dumpi_to_graph/build/dumpi_to_graph
dumpi_to_graph_config=${anacin_x_root}/submodules/dumpi_to_graph/config/dumpi_and_csmpi.json

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

    # Generate CSMPI config for this run
    ${csmpi_config_generator} -o ${run_dir}/csmpi_config.json -d ${run_dir}/csmpi -f ${csmpi_config_functions} -b "glibc" 

    # Generate the job scripts for this run
    ${job_script_generator} ${anacin_x_root} \
                            ${run_dir} \
                            ${n_procs_per_node} \
                            ${load_balancing_policy} \
                            ${load_balancing_threshold} \
                            ${refinement_policy} \
                            ${refinement_frequency} \
                            ${slicing_policy} \
                            --with_csmpi \
                            --with_ninja \
                            --transform_slices "comm_channel" \
                            --trace_n_procs 16 \
                            --build_graph_n_procs 16 \
                            --extract_slices_n_procs 16 \
                            --transform_slices_n_procs 16


    # Set location of tracing job
    if [ ${multi_node_runs} -eq 1 ]
    then
        trace_job=${run_dir}/trace_multi_node.sh
        n_nodes_tracing=16
    else
        trace_job=${run_dir}/trace_single_node.sh
        n_nodes_tracing=1
    fi

    # Set location of other jobs
    build_graph_job=${run_dir}/build_graph.sh
    merge_barriers_job=${run_dir}/merge_barriers.sh
    extract_slices_job=${run_dir}/extract_slices.sh
    transform_slices_job=${run_dir}/transform_slices.sh

    # Trace the application
    trace_job_stdout=$( bsub < ${trace_job} )
    trace_job_id=$( echo ${trace_job_stdout} | sed 's/[^0-9]*//g' )

    # Construct the event graph for this run
    build_graph_job_stdout=$( bsub -w ${trace_job_id} < ${build_graph_job} )
    build_graph_job_id=$( echo ${build_graph_job_stdout} | sed 's/[^0-9]*//g' )
    
    # Merge consecutive barrier nodes together in event graph
    event_graph=${run_dir}/event_graph.graphml
    merge_barriers_job_stdout=$( bsub -w ${build_graph_job_id} < ${merge_barriers_job} )
    merge_barriers_job_id=$( echo ${merge_barriers_job_stdout} | sed 's/[^0-9]*//g' )

    # Extract slices
    event_graph=${run_dir}/event_graph_squashed.graphml
    extract_slices_stdout=$( bsub -w ${merge_barriers_job_id} < ${extract_slices_job} )
    extract_slices_job_id=$( echo ${extract_slices_stdout} | sed 's/[^0-9]*//g' )

    # Transform each slice from event graph representation to communication channel graph representation
    transform_slices_stdout=$( bsub -w ${extract_slices_job_id} < ${transform_slices_job} )
    transform_slices_job_id=$( echo ${transform_slices_stdout} | sed 's/[^0-9]*//g' )
done
