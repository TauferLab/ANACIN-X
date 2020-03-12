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
    results_root="/p/lscratchh/chapp1/comm_patterns/rempi_study/"
fi

# Comm pattern proxy app
app=${anacin_x_root}/apps/comm_pattern_generator/build_${system}/comm_pattern_generator
job_script_record_pack_procs=${anacin_x_root}/apps/comm_pattern_generator/record_pattern_pack_procs.sh
job_script_record_spread_procs=${anacin_x_root}/apps/comm_pattern_generator/record_pattern_spread_procs.sh

# Convenience function for making the dependency lists for postprocessing jobs
# time series job
function join_by { local IFS="$1"; shift; echo "$*"; }

# Parameter space for study
patterns=("naive_reduce")
proc_placement=("pack")
run_scales=(21)
nd_percentages=("20" "30" "40" "50" "60" "70" "80" "90" "100")
#nd_percentages=("100")

for pattern in ${patterns[@]};
do
    for proc_placement in ${proc_placement[@]};
    do
        for n_procs in ${run_scales[@]};
        do
            for nd_percentage in ${nd_percentages[@]};
            do
                echo "Launching jobs for: proc. placement = ${proc_placement}, # procs. = ${n_procs}, ND% = ${nd_percentage}"
                runs_root=${results_root}/n_procs_${n_procs}/proc_placement_${proc_placement}/nd_percentage_${nd_percentage}/

                analysis_job_deps=()
                for run_idx in `seq -f "%03g" ${run_idx_low} ${run_idx_high}`; 
                do
                    # Set up results dir
                    run_dir=${runs_root}/run_${run_idx}/
                    mkdir -p ${run_dir}
                    cd ${run_dir}
                    # Determine config
                    if [ ${pattern} == "naive_reduce" ]; then
                        config=${anacin_x_root}/apps/comm_pattern_generator/config/rempi_study_${pattern}_nd_percentage_${nd_percentage}.json
                    elif [ ${pattern} == "amg2013" ]; then
                        config=${anacin_x_root}/apps/comm_pattern_generator/config/rempi_study_${pattern}_nd_percentage_${nd_percentage}.json
                    fi
                    # Record execution
                    if [ ${proc_placement} == "pack" ]; then
                        n_nodes_record=$(echo "(${n_procs} + ${n_procs_per_node} - 1)/${n_procs_per_node}" | bc)
                        #record_stdout=$( sbatch -N${n_nodes_record} ${job_script_record_pack_procs} ${n_procs} ${app} ${config} ${run_dir})
                        ${job_script_record_pack_procs} ${n_nodes_record} ${n_procs} ${app} ${config} ${run_dir} >& ${run_dir}/component_sizes.log
                    elif [ ${proc_placement} == "spread" ]; then
                        n_nodes_record=${n_procs}
                        record_stdout=$( sbatch -N${n_nodes_record} ${job_script_record_spread_procs} ${n_procs} ${app} ${config} ${run_dir})
                    fi
                    record_job_id=$( echo ${record_stdout} | sed 's/[^0-9]*//g' )
                    analysis_job_deps+=(${record_job_id})
                    echo "Done with job ${run_idx} of ${run_idx_high}"
                done # runs

                # Extract recording cost statistics and generate visualizations
                analysis_job_dep_str=$( join_by : ${analysis_job_deps[@]} )
                cd ${runs_root}
            done # msg sizes
        done # num procs
    done # proc placement
done # patterns
