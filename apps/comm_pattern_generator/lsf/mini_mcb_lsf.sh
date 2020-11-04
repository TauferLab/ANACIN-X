#!/usr/bin/env bash

run_idx_low=$1
run_idx_high=$2
n_nodes=$3
n_iters=$4
n_procs=$5
results_root=$6
#run_scales=$6

#echo "sourcing"
#source ./lsf_kae_paths.config
source ./example_paths_lsf.config
echo "done" sourcing

# Convenience function for making the dependency lists for the kernel distance
# time series job
#function join_by { local IFS="$1"; shift; echo "$*"; }
function join_by { local d=$1; shift; local f=$1; shift; printf %s "$f" "${@/#/$d}"; }

#proc_placement=("pack" "spread")
#run_scales=(11 21 41 81)
#message_sizes=(1 512 1024 2048)

#proc_placement=("pack")
#run_scales=(11)
#message_sizes=(1)

#proc_placement=("pack" "spread")
#run_scales=(36)
#interleave_options=("non_interleaved" "interleaved")

#proc_placement=("pack", "spread")
proc_placement=("pack")
run_scales=(32)
#interleave_options=("non_interleaved")
interleave_options=("interleaved" "non_interleaved")


echo "before the loops"
#for iters in ${n_iters[@]};
#do
for proc_placement in ${proc_placement[@]};
do
    #    for n_procs in ${run_scales[@]};
    #    do
    for option in ${interleave_options[@]};
    do
	echo "Launching jobs for: proc. placement = ${proc_placement}, # procs. = ${n_procs}, interleaving?  ${option}"
	runs_root=${results_root}/n_procs_${n_procs}/proc_placement_${proc_placement}/interleave_option_${option}/

	# Launch intra-execution jobs
	kdts_job_deps=()
	for run_idx in `seq -f "%03g" ${run_idx_low} ${run_idx_high}`; 
	do

	    # Set up results dir
	    run_dir=${runs_root}/run_${run_idx}/
	    mkdir -p ${run_dir}
	    cd ${run_dir}
	    #		echo "Entering submission of generator"
	    
	    # Determine interleaving number
#	    if [ ${option} == "interleaved" ]; then
#		interleaving=1
#	    elif [ ${option} == "non_interleaved" ]; then
#		interleaving=0
#	    fi

	    # Create config if doesn't exist
	    config=${anacin_x_root}/apps/comm_pattern_generator/config/mini_mcb_${option}_niters_${n_iters}.json
#	    if [ ! -f "config" ]; then
#		python3 > ${debugging_path}/create_json_output.txt 2> ${debugging_path}/create_json_error.txt ${anacin_x_root}/apps/comm_pattern_generator/config/json_gen.py "mini_mcb" ${interleaving} ${n_iters}
#	    fi

	    # Trace execution
	    if [ ${proc_placement} == "pack" ]; then
		#n_nodes_trace=$(echo "(${n_procs} + ${n_procs_per_node} - 1)/${n_procs_per_node}" | bc)
		#echo "Starting Trace Execution"
		echo ${n_procs}
		trace_stdout=$( bsub -n ${n_procs} -R "span[ptile=32]" -o ${debugging_path}/trace_exec_output.txt -e ${debugging_path}/trace_exec_error.txt ${job_script_trace_pack_procs} ${n_procs} ${app} ${config} )
	    elif [ ${proc_placement} == "spread" ]; then
		n_nodes_trace=${n_procs}
		#trace_stdout=$( bsub -nnodes ${n_nodes_trace} ${job_script_trace_spread_procs} ${n_procs} ${app} ${config} )
	    fi
	    trace_job_id=$( echo ${trace_stdout} | sed 's/[^0-9]*//g' )
	    #		echo "$trace_job_id is the id for this run of the tracer."
	    
	    echo ${n_procs}
	    # Build event graph
	    #n_nodes_build_graph=$(echo "(${n_procs} + ${n_procs_per_node} - 1)/${n_procs_per_node}" | bc)
	    #ptile_arg=$(echo "${n_procs} / ${n_nodes}" | bc)
	    build_graph_stdout=$( bsub -n ${n_procs} -R "span[ptile=32]" -w "done(${trace_job_id})" -o ${debugging_path}/build_graph_output.txt -e ${debugging_path}/build_graph_error.txt ${job_script_build_graph} ${n_procs} ${dumpi_to_graph_bin} ${dumpi_to_graph_config} ${run_dir} )
	    build_graph_job_id=$( echo ${build_graph_stdout} | sed 's/[^0-9]*//g' )
	    event_graph=${run_dir}/event_graph.graphml
	    #		echo "exiting graph build"
	    
	    # Extract slices
	    extract_slices_stdout=$( bsub -n ${n_procs} -R "span[ptile=32]" -w "done(${build_graph_job_id})" -o ${debugging_path}/extract_slices_output.txt -e ${debugging_path}/extract_slices_error.txt ${job_script_extract_slices} ${n_procs_extract_slices} ${extract_slices_script} ${event_graph} ${slicing_policy} )
	    extract_slices_job_id=$( echo ${extract_slices_stdout} | sed 's/[^0-9]*//g' ) 
	    kdts_job_deps+=("done(${extract_slices_job_id})")
	    #		echo "exiting slice extraction"

	done # runs
	#	    echo "entering kdts"
	
	# Compute kernel distances for each slice
	kdts_job_dep_str=$( join_by "&&" ${kdts_job_deps[@]} )
	#echo ${kdts_job_dep_str}
	cd ${runs_root}
	compute_kdts_stdout=$( bsub -n ${n_procs} -R "span[ptile=32]" -w ${kdts_job_dep_str} -o ${debugging_path}/compute_kdts_output.txt -e ${debugging_path}/compute_kdts_error.txt ${job_script_compute_kdts} ${n_procs_compute_kdts} ${compute_kdts_script} ${runs_root} ${graph_kernel} ${slicing_policy} )
	#	    echo "exiting kdts"        
	#compute_kdts_stdout=$( sbatch -N${n_nodes_compute_kdts} ${job_script_compute_kdts} ${n_procs_compute_kdts} ${compute_kdts_script} ${runs_root} ${graph_kernel} )
	compute_kdts_job_id=$( echo ${compute_kdts_stdout} | sed 's/[^0-9]*//g' )
	#	    echo "job id calc"
	
	## Generate plot
	#make_plot_stdout=$( sbatch -N1 --dependency=afterok:${compute_kdts_job_id} ${job_script_make_plot} ${make_plot_script_mini_mcb} "${runs_root}/kdts.pkl" )
	##make_plot_stdout=$( sbatch -N1 ${job_script_make_plot} ${make_plot_script_mini_mcb} "${runs_root}/kdts.pkl" )

    done # msg sizes
    #    done # num procs
done # proc placement
#done
