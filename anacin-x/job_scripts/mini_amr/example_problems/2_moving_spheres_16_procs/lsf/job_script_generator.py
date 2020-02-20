#!/usr/bin/env python3

import argparse 
import os

def generate_trace_job( repo_root_dir,
                        trace_dir,
                        load_balancing_policy,
                        load_balancing_threshold,
                        refinement_policy,
                        refinement_frequency,
                        multi_node,
                        with_csmpi,
                        with_ninja,
                        n_procs,
                        n_procs_per_node):
    if multi_node:
        script_path = os.getcwd() + "/trace_multi_node.sh"
    else:
        script_path = os.getcwd() + "/trace_single_node.sh"

    hashbang_line = [ "#!/usr/bin/env bash" ]
    bsub_directive_lines = [ "#BSUB -n " + str(n_procs),
                             "#BSUB -W 30:00",
                             "#BSUB -o trace_mini_amr_%J.out",
                             "#BSUB -e trace_mini_amr_%J.err" ]
    if multi_node:
        bsub_directive_lines.append( "#BSUB -R \"span[ptile=1]\"" )
    else:
        if n_procs < n_procs_per_node:
            bsub_directive_lines.append( "#BSUB -R \"span[ptile=" + str(n_procs) + "]\"" )
        else:
            bsub_directive_lines.append( "#BSUB -R \"span[ptile=" + str(n_procs_per_node) + "]\"" )

    # The following lines define: 
    # - Configuration of miniAMR 
    # - Configuration of the tracing module stack
    config_lines = [ "anacin_x_root=" + repo_root_dir,
                     "mini_amr_bin=${anacin_x_root}/apps/miniAMR/ref/ma.x",
                     "load_balancing_policy=" + str(load_balancing_policy),
                     "load_balancing_threshold=\"" + str(load_balancing_threshold) + "\"",
                     "refinement_policy=" + str(refinement_policy),
                     "refinement_frequency=" + str(refinement_frequency),
                     "pnmpi=${anacin_x_root}/submodules/PnMPI/build/lib/libpnmpi.so",
                     "pnmpi_lib_path=${anacin_x_root}/anacin-x/job_scripts/pnmpi_patched_libs/" ]
    if with_csmpi and with_ninja:
        config_lines += [ "pnmpi_conf=${anacin_x_root}/anacin-x/job_scripts/pnmpi_configs/dumpi_csmpi_ninja.conf",
                          "csmpi_config=" + trace_dir + "/csmpi_config.json" ]
    elif with_csmpi and not with_ninja:
        config_lines += [ "pnmpi_conf=${anacin_x_root}/anacin-x/job_scripts/pnmpi_configs/dumpi_csmpi.conf",
                          "csmpi_config=" + trace_dir + "/csmpi_config.json" ]
    elif not with_csmpi and with_ninja:
        config_lines.append( "pnmpi_conf=${anacin_x_root}/anacin-x/job_scripts/pnmpi_configs/dumpi_ninja.conf" )
    else:
        config_lines.append( "pnmpi_conf=${anacin_x_root}/anacin-x/job_scripts/pnmpi_configs/dumpi.conf" )
                     
    # The following lines define how the job is launched
    launch_job_lines = [ "LD_PRELOAD=${pnmpi} PNMPI_LIB_PATH=${pnmpi_lib_path} PNMPI_CONF=${pnmpi_conf} CSMPI_CONFIG=${csmpi_config} mpirun -np 16 ${mini_amr_bin} \\",
                         "\t--num_refine 4 \\",
                         "\t--max_blocks 4000 \\",
                         "\t--init_x 1 \\",
                         "\t--init_y 1 \\",
                         "\t--init_z 1 \\",
                         "\t--npx 4 \\",
                         "\t--npy 2 \\",
                         "\t--npz 2 \\",
                         "\t--nx 8 \\",
                         "\t--ny 8 \\",
                         "\t--nz 8 \\",
                         "\t--num_objects 2 \\",
                         "\t--object 2 0 -1.10 -1.10 -1.10 0.030 0.030 0.030 1.5 1.5 1.5 0.0 0.0 0.0 \\",
                         "\t--object 2 0 0.5 0.5 1.76 0.0 0.0 -0.025 0.75 0.75 0.75 0.0 0.0 0.0 \\",
                         "\t--num_tsteps 20 \\",
                         "\t--checksum_freq 4 \\",
                         "\t--stages_per_ts 16 \\",
                         "\t--lb_opt ${load_balancing_policy} \\",
                         "\t--inbalance ${load_balancing_threshold} \\",
                         "\t--uniform_refine ${refinement_policy} \\" ]
    if refinement_policy != 1:
        launch_job_lines.append( "\t--refine_freq ${refinement_frequency}" )
    
    # Write the job script
    with open( script_path, "w" ) as outfile:
        outfile.write( hashbang_line[0] + "\n" )
        for line in bsub_directive_lines:
            outfile.write( line + "\n" )
        for line in config_lines:
            outfile.write( line + "\n" )
        for line in launch_job_lines:
            outfile.write( line + "\n" )


def generate_build_graph_job( repo_root_dir, trace_dir, n_procs, n_procs_per_node ):
    script_path = os.getcwd() + "/build_graph.sh"

    hashbang_line = [ "#!/usr/bin/env bash" ]
    bsub_directive_lines = [ "#BSUB -n " + str(n_procs),
                             "#BSUB -W 10",
                             "#BSUB -o build_graph_%J.out",
                             "#BSUB -e build_graph_%J.err" ]
    if n_procs < n_procs_per_node:                         
        bsub_directive_lines.append( "#BSUB -R \"span[ptile=" + str(n_procs) + "]\"" )
    else:
        bsub_directive_lines.append( "#BSUB -R \"span[ptile=" + str(n_procs_per_node) + "]\"" )

    config_lines = [ "anacin_x_root=" + repo_root_dir,
                     "dumpi_to_graph_bin=${anacin_x_root}/submodules/dumpi_to_graph/build/dumpi_to_graph",
                     "dumpi_to_graph_config=${anacin_x_root}/submodules/dumpi_to_graph/config/dumpi_and_csmpi.json ",
                     "trace_dir=" + trace_dir ]

    launch_job_lines = [ "mpirun -np " + str(n_procs) + " ${dumpi_to_graph_bin} ${dumpi_to_graph_config} ${trace_dir}" ]

    # Write the job script
    with open( script_path, "w" ) as outfile:
        outfile.write( hashbang_line[0] + "\n" )
        for line in bsub_directive_lines:
            outfile.write( line + "\n" )
        for line in config_lines:
            outfile.write( line + "\n" )
        for line in launch_job_lines:
            outfile.write( line + "\n" )


def generate_merge_barriers_job( repo_root_dir, trace_dir ):
    script_path = os.getcwd() + "/merge_barriers.sh"
    hashbang_line = [ "#!/usr/bin/env bash" ]
    bsub_directive_lines = [ "#BSUB -n 1",
                             "#BSUB -W 10",
                             "#BSUB -R \"span[ptile=1]\"",
                             "#BSUB -o merge_barriers_%J.out",
                             "#BSUB -e merge_barriers_%J.err" ]
    merge_barriers_script = repo_root_dir + "/anacin-x/event_graph_analysis/merge_barriers.py"
    config_lines = [ "trace_dir=" + trace_dir ]
    launch_job_lines = [ merge_barriers_script + " ${trace_dir}/event_graph.graphml" ]
    # Write the job script
    with open( script_path, "w" ) as outfile:
        outfile.write( hashbang_line[0] + "\n" )
        for line in bsub_directive_lines:
            outfile.write( line + "\n" )
        for line in config_lines:
            outfile.write( line + "\n" )
        for line in launch_job_lines:
            outfile.write( line + "\n" )


def generate_extract_slices_job( repo_root_dir, trace_dir, slicing_policy_path, n_procs, n_procs_per_node ):
    script_path = os.getcwd() + "/extract_slices.sh"
    hashbang_line = [ "#!/usr/bin/env bash" ]
    bsub_directive_lines = [ "#BSUB -n " + str(n_procs),
                             "#BSUB -W 960",
                             "#BSUB -o extract_slices_%J.out",
                             "#BSUB -e extract_slices_%J.err" ]
    if n_procs < n_procs_per_node:                         
        bsub_directive_lines.append( "#BSUB -R \"span[ptile=" + str(n_procs) + "]\"" )
    else:
        bsub_directive_lines.append( "#BSUB -R \"span[ptile=" + str(n_procs_per_node) + "]\"" )
    config_lines = [ "extract_slices_script=" + repo_root_dir + "/anacin-x/event_graph_analysis/extract_slices.py",
                     "event_graph=" + trace_dir + "/event_graph_merged_barriers.graphml",
                     "slicing_policy=" + slicing_policy_path ]
    launch_job_lines = [ "mpirun -np " + str(n_procs) +  " ${extract_slices_script} ${event_graph} ${slicing_policy}" ]
    with open( script_path, "w" ) as outfile:
        outfile.write( hashbang_line[0] + "\n" )
        for line in bsub_directive_lines:
            outfile.write( line + "\n" )
        for line in config_lines:
            outfile.write( line + "\n" )
        for line in launch_job_lines:
            outfile.write( line + "\n" )


def generate_transform_slices_job( repo_root_dir, trace_dir, transform, n_procs, n_procs_per_node ):
    script_path = os.getcwd() + "/transform_slices.sh"
    hashbang_line = [ "#!/usr/bin/env bash" ]
    bsub_directive_lines = [ "#BSUB -n " + str(n_procs),
                             "#BSUB -W 960",
                             "#BSUB -o transform_slices_%J.out",
                             "#BSUB -e transform_slices_%J.err" ]
    if n_procs < n_procs_per_node:                         
        bsub_directive_lines.append( "#BSUB -R \"span[ptile=" + str(n_procs) + "]\"" )
    else:
        bsub_directive_lines.append( "#BSUB -R \"span[ptile=" + str(n_procs_per_node) + "]\"" )
    config_lines = [ "transform_slices_script=" + repo_root_dir + "/anacin-x/event_graph_analysis/transform_slices.py",
                     "slice_dir=" + trace_dir + "/slices/",
                     "transform=" + "\"" + str(transform) + "\"" ]
    launch_job_lines = [ "mpirun -np " + str(n_procs) +  " ${transform_slices_script} ${slice_dir} ${transform}" ]
    with open( script_path, "w" ) as outfile:
        outfile.write( hashbang_line[0] + "\n" )
        for line in bsub_directive_lines:
            outfile.write( line + "\n" )
        for line in config_lines:
            outfile.write( line + "\n" )
        for line in launch_job_lines:
            outfile.write( line + "\n" )

if __name__ == "__main__":
    desc = ""
    parser = argparse.ArgumentParser( description = desc )

    parser.add_argument("repo_root_dir")
    parser.add_argument("trace_dir")

    parser.add_argument("n_procs_per_node",
                        help="Number of processes that can be run on a single compute node")

    # miniAMR execution parameters
    parser.add_argument("load_balancing_policy", type=int,
                        help="Off: 0, Once per refinement step: 1, Once per refinement substep: 2")
    parser.add_argument("load_balancing_threshold", type=float,
                        help="Percentage imbalance threshold that must be met to trigger load-balancing")
    parser.add_argument("refinement_policy", type=int,
                        help="Domain-Determined Refinement: 0, Uniform Refinement: 1")
    parser.add_argument("refinement_frequency", type=int,
                        help="If using non-uniform refinement, how many time steps will occur before a mesh refinement")
    
    # Specify the slicing policy that will be used to partition the event graph
    parser.add_argument("slicing_policy",
                        help="Path to slicing policy definition file")
   
    # Workflow parameters
    parser.add_argument("--multi_node", required=False, default=False, action="store_true",
                        help="Run each MPI process in the traced run on a separate compute node. (Optional)")
    parser.add_argument("--with_csmpi", required=False, default=False, action="store_true",
                        help="Trace callstacks via CSMPI as well as communication via DUMPI. (Optional)")
    parser.add_argument("--with_ninja", required=False, default=False, action="store_true",
                        help="Run tracing stage with noise-injection via NINJA")
    parser.add_argument("--transform_slices", required=False, default=None,
                        help="Specify a transformation to be applied to each slice. (Optional)")
    
    # Arguments specifying resource usage for each job script
    parser.add_argument("--trace_n_procs", required=False, default=16,
                        help="Number of processes to run the tracing stage on")
    parser.add_argument("--build_graph_n_procs", required=False, default=16,
                        help="Number of processes to run the event graph construction stage on")
    parser.add_argument("--extract_slices_n_procs", required=False, default=16,
                        help="Number of processes to run the slice extraction stage on")
    parser.add_argument("--transform_slices_n_procs", required=False, default=16,
                        help="Number of processes to run the slice transformation stage on")

    args = parser.parse_args()

    repo_root_dir = os.path.abspath( args.repo_root_dir )
    trace_dir = os.path.abspath( args.trace_dir )
    slicing_policy_path = os.path.abspath( args.slicing_policy )

    generate_trace_job( repo_root_dir,
                        trace_dir,
                        args.load_balancing_policy,
                        args.load_balancing_threshold,
                        args.refinement_policy,
                        args.refinement_frequency,
                        args.multi_node,
                        args.with_csmpi,
                        args.with_ninja,
                        args.trace_n_procs,
                        args.n_procs_per_node )
    
    generate_build_graph_job( repo_root_dir, 
                              trace_dir,
                              args.build_graph_n_procs,
                              args.n_procs_per_node )

    generate_merge_barriers_job( repo_root_dir, 
                                 trace_dir )

    generate_extract_slices_job( repo_root_dir,
                                 trace_dir,
                                 slicing_policy_path,
                                 args.extract_slices_n_procs,
                                 args.n_procs_per_node )

    generate_transform_slices_job( repo_root_dir,
                                   trace_dir,
                                   args.transform_slices,
                                   args.transform_slices_n_procs,
                                   args.n_procs_per_node )

