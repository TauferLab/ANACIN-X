#!/usr/bin/env bash

run_idx_low=$1
run_idx_high=$2
results_root=$3

source ./example_paths.config

# Convenience function for making the dependency lists for the kernel distance
# time series job
function join_by { local IFS="$1"; shift; echo "$*"; }

#proc_placement=("pack" "spread")
proc_placement=("pack")
run_scales=(36)
message_sizes=(1)
nd_neighbor_fractions=("0" "0.25" "0.5" "0.75" "1")
#nd_neighbor_fractions=("0")

for proc_placement in ${proc_placement[@]};
do
    for n_procs in ${run_scales[@]};
    do
        for nd_neighbor_fraction in ${nd_neighbor_fractions[@]};
        do
            for msg_size in ${message_sizes[@]};
            do
                echo "Launching jobs for: proc. placement = ${proc_placement}, # procs. = ${n_procs}, neighbor non-determinism fraction = ${nd_neighbor_fraction}, msg. size = ${msg_size}"
                runs_root=${results_root}/n_procs_${n_procs}/proc_placement_${proc_placement}/neighbor_nd_fraction_${nd_neighbor_fraction}/msg_size_${msg_size}/

                # Launch intra-execution jobs
                kdts_job_deps=()
                for run_idx in `seq -f "%03g" ${run_idx_low} ${run_idx_high}`; 
                do
                    # Set up results dir
                    run_dir=${runs_root}/run_${run_idx}/
                    mkdir -p ${run_dir}
                    cd ${run_dir}
                    
                    # Determine proc grid
                    if [ ${n_procs} == 36 ]; then
                        proc_grid="4x3x2"
                    else
                        echo "Invalid # procs: ${n_procs}"
                        exit
                    fi

                    # Trace execution
                    config=${anacin_x_root}/apps/comm_pattern_generator/config/unstructured_mesh_${proc_grid}_nd_neighbor_fraction_${nd_neighbor_fraction}_msg_size_${msg_size}.json
                    if [ ${proc_placement} == "pack" ]; then
                        n_nodes_trace=$(echo "(${n_procs} + ${n_procs_per_node} - 1)/${n_procs_per_node}" | bc)
                        trace_stdout=$( sbatch -N${n_nodes_trace} ${job_script_trace_pack_procs} ${n_procs} ${app} ${config} )
                    elif [ ${proc_placement} == "spread" ]; then
                        n_nodes_trace=${n_procs}
                        trace_stdout=$( sbatch -N${n_nodes_trace} ${job_script_trace_spread_procs} ${n_procs} ${app} ${config} )
                    fi
                    trace_job_id=$( echo ${trace_stdout} | sed 's/[^0-9]*//g' )
                    
                    # Build event graph
                    n_nodes_build_graph=$(echo "(${n_procs} + ${n_procs_per_node} - 1)/${n_procs_per_node}" | bc)
                    build_graph_stdout=$( sbatch -N${n_nodes_build_graph} --dependency=afterok:${trace_job_id} ${job_script_build_graph} ${n_procs} ${dumpi_to_graph_bin} ${dumpi_to_graph_config} ${run_dir} )
                    build_graph_job_id=$( echo ${build_graph_stdout} | sed 's/[^0-9]*//g' )
                    event_graph=${run_dir}/event_graph.graphml

                    # Extract slices
                    extract_slices_stdout=$( sbatch -N${n_nodes_extract_slices} --dependency=afterok:${build_graph_job_id} ${job_script_extract_slices} ${n_procs_extract_slices} ${extract_slices_script} ${event_graph} ${slicing_policy} )
                    extract_slices_job_id=$( echo ${extract_slices_stdout} | sed 's/[^0-9]*//g' ) 
                    kdts_job_deps+=(${extract_slices_job_id})
                done # runs

                # Compute kernel distances for each slice
                kdts_job_dep_str=$( join_by : ${kdts_job_deps[@]} )
                cd ${runs_root}
                compute_kdts_stdout=$( sbatch -N${n_nodes_compute_kdts} --dependency=afterok:${kdts_job_dep_str} ${job_script_compute_kdts} ${n_procs_compute_kdts} ${compute_kdts_script} ${runs_root} ${graph_kernel} )
                #compute_kdts_stdout=$( sbatch -N${n_nodes_compute_kdts} ${job_script_compute_kdts} ${n_procs_compute_kdts} ${compute_kdts_script} ${runs_root} ${graph_kernel} )
                compute_kdts_job_id=$( echo ${compute_kdts_stdout} | sed 's/[^0-9]*//g' )

                # Generate plot
                make_plot_stdout=$( sbatch -N1 --dependency=afterok:${compute_kdts_job_id} ${job_script_make_plot} ${make_plot_script_unstructured_mesh} "${runs_root}/kdts.pkl" ${nd_neighbor_fraction})
                #make_plot_stdout=$( sbatch -N1 ${job_script_make_plot} ${make_plot_script_unstructured_mesh} "${runs_root}/kdts.pkl" )

            done # msg sizes
        done # nd neighbor fraction
    done # num procs
done # proc placement
