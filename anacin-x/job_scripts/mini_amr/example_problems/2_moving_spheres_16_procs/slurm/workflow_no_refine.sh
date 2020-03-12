#!/usr/bin/env bash

run_idx_low=$1
run_idx_high=$2

# Orient ourselves
anacin_x_root=$HOME/ANACIN-X
system=$(hostname | sed 's/[0-9]*//g')
# Determine node capacity
if [ ${system} == "quartz" ]; then
    n_procs_per_node=36
elif [ ${system} == "catalyst" ]; then
    n_procs_per_node=24
fi
# Determine where to write results data (trace files, event graphs, etc.)
if [ ${system} == "quartz" ] || [ ${system} == "catalyst" ]; then
    results_root="/p/lscratchh/chapp1/mini_amr/system_${system}/nprocs_16_2_moving_spheres/"
fi

job_scripts_root=${anacin_x_root}/anacin-x/job_scripts/mini_amr/example_problems/2_moving_spheres_16_procs/slurm/

# Comm pattern proxy app
app=${anacin_x_root}/apps/miniAMR/ref/ma.x
job_script_trace_pack_procs=${job_scripts_root}/trace_no_refine_pack_procs.sh
job_script_trace_spread_procs=${job_scripts_root}/trace_no_refine_spread_procs.sh
gen_csmpi_config=${anacin_x_root}/submodules/csmpi/config/generate_config.py
csmpi_mini_amr_functions=${anacin_x_root}/submodules/csmpi/config/mpi_function_subsets/mini_amr.json

# Event graph construction
dumpi_to_graph_bin=${anacin_x_root}/submodules/dumpi_to_graph/build_${system}/dumpi_to_graph
dumpi_to_graph_config=${anacin_x_root}/submodules/dumpi_to_graph/config/dumpi_and_csmpi_all_blocking_collectives.json
job_script_build_graph=${job_scripts_root}/build_graph.sh

# Event graph postprocessing
merge_barriers_script=${anacin_x_root}/anacin-x/event_graph_analysis/merge_barriers.py
job_script_merge_barriers=${job_scripts_root}/merge_barriers.sh

# Slice extraction
extract_slices_script=${anacin_x_root}/anacin-x/event_graph_analysis/extract_slices.py
slicing_policy=${anacin_x_root}/anacin-x/event_graph_analysis/slicing_policies/barrier_delimited_full.json
job_script_extract_slices=${job_scripts_root}/extract_slices.sh
n_procs_extract_slices=36
n_nodes_extract_slices=$(echo "(${n_procs_extract_slices} + ${n_procs_per_node} - 1)/${n_procs_per_node}" | bc)

# Convenience function for making the dependency lists for the kernel distance
# time series job
function join_by { local IFS="$1"; shift; echo "$*"; }

# Kernel distance time series computation
compute_kdts_script=${anacin_x_root}/anacin-x/event_graph_analysis/compute_kernel_distance_time_series.py
job_script_compute_kdts=${job_scripts_root}/compute_kdts.sh
n_procs_compute_kdts=36
n_nodes_compute_kdts=$(echo "(${n_procs_compute_kdts} + ${n_procs_per_node} - 1)/${n_procs_per_node}" | bc)

# Define which graph kernels we'll compute KDTS for 
#graph_kernel=${anacin_x_root}/anacin-x/event_graph_analysis/graph_kernel_policies/wlst_5iters_logical_timestamp_label.json
graph_kernel=${anacin_x_root}/anacin-x/event_graph_analysis/graph_kernel_policies/test_kernels.json

## Visualizations
#make_plot_script=${anacin_x_root}/anacin-x/event_graph_analysis/visualization/make_naive_reduce_example_plot.py
#job_script_make_plot=${job_scripts_root}/make_plot.sh

proc_placement=("pack" "spread")
#proc_placement=("spread")

for proc_placement in ${proc_placement[@]};
do
    echo "Launching jobs for: proc. placement = ${proc_placement}"
    runs_root=${results_root}/no_refine/proc_placement_${proc_placement}/

    # Launch intra-execution jobs
    kdts_job_deps=()
    #for run_idx in `seq -f "%03g" ${run_idx_low} ${run_idx_high}`; 
    #do
    #    # Set up results dir
    #    run_dir=${runs_root}/run_${run_idx}/
    #    mkdir -p ${run_dir}
    #    cd ${run_dir}
    #    
    #    # Generate CSMPI configuration
    #    csmpi_dir=${run_dir}/csmpi/
    #    csmpi_config=${run_dir}/csmpi_config.json
    #    ${gen_csmpi_config} -o ${csmpi_config} -f ${csmpi_mini_amr_functions} -d ${csmpi_dir} 

    #    # Trace execution
    #    if [ ${proc_placement} == "pack" ]; then
    #        trace_stdout=$( sbatch -N1 ${job_script_trace_pack_procs} ${app} ${csmpi_config})
    #    elif [ ${proc_placement} == "spread" ]; then
    #        trace_stdout=$( sbatch -N16 ${job_script_trace_spread_procs} ${app} ${csmpi_config})
    #    fi
    #    trace_job_id=$( echo ${trace_stdout} | sed 's/[^0-9]*//g' )
    #    
    #    # Build event graph
    #    build_graph_stdout=$( sbatch -N1 --dependency=afterok:${trace_job_id} ${job_script_build_graph} ${dumpi_to_graph_bin} ${dumpi_to_graph_config} ${run_dir} )
    #    build_graph_job_id=$( echo ${build_graph_stdout} | sed 's/[^0-9]*//g' )
    #    event_graph=${run_dir}/event_graph.graphml

    #    # Merge adjacent barriers
    #    merge_barriers_stdout=$( sbatch -N1 --dependency=afterok:${build_graph_job_id} ${job_script_merge_barriers} ${merge_barriers_script} ${event_graph} )
    #    merge_barriers_job_id=$( echo ${merge_barriers_stdout} | sed 's/[^0-9]*//g' )
    #    merged_event_graph=${run_dir}/event_graph_merged_barriers.graphml
    #        
    #    # Extract slices
    #    extract_slices_stdout=$( sbatch -N${n_nodes_extract_slices} --dependency=afterok:${merge_barriers_job_id} ${job_script_extract_slices} ${n_procs_extract_slices} ${extract_slices_script} ${merged_event_graph} ${slicing_policy} )
    #    extract_slices_job_id=$( echo ${extract_slices_stdout} | sed 's/[^0-9]*//g' ) 
    #    kdts_job_deps+=(${extract_slices_job_id})
    #done # runs

    # Compute kernel distances for each slice
    kdts_job_dep_str=$( join_by : ${kdts_job_deps[@]} )
    cd ${runs_root}
    #compute_kdts_stdout=$( sbatch -N${n_nodes_compute_kdts} --dependency=afterok:${kdts_job_dep_str} ${job_script_compute_kdts} ${n_procs_compute_kdts} ${compute_kdts_script} ${runs_root} ${graph_kernel} )
    compute_kdts_stdout=$( sbatch -N${n_nodes_compute_kdts} ${job_script_compute_kdts} ${n_procs_compute_kdts} ${compute_kdts_script} ${runs_root} ${graph_kernel} )
    compute_kdts_job_id=$( echo ${compute_kdts_stdout} | sed 's/[^0-9]*//g' )

    # Generate plot
    #make_plot_stdout=$( sbatch -N1 --dependency=afterok:${compute_kdts_job_id} ${job_script_make_plot} ${make_plot_script} "${runs_root}/kdts.pkl" )
    #make_plot_stdout=$( sbatch -N1 ${job_script_make_plot} ${make_plot_script} "${runs_root}/kdts.pkl" )
done # proc placement
