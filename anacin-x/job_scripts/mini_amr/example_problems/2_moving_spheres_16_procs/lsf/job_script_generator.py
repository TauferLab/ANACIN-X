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
                        with_csmpi ):
    if multi_node:
        script_path = os.getcwd() + "/trace_multi_node.sh"
    else:
        script_path = os.getcwd() + "/trace_single_node.sh"

    hashbang_line = [ "#!/usr/bin/env bash" ]
    bsub_directive_lines = [ "#BSUB -n 16",
                             "#BSUB -W 30:00",
                             "#BSUB -o trace_mini_amr_%J.out",
                             "#BSUB -e trace_mini_amr_%J.err" ]
    if multi_node:
        bsub_directive_lines.append( "#BSUB -R \"span[ptile=1]\"" )
    else:
        bsub_directive_lines.append( "#BSUB -R \"span[ptile=16]\"" )

    # The following lines define: 
    # - Configuration of miniAMR 
    # - Configuration of the tracing module stack
    config_lines = [ "anacin_x_root=" + repo_root_dir,
                     "mini_amr_bin=${anacin_x_root}/apps/miniAMR/ref/ma.x",
                     "load_balancing_policy=" + str(load_balancing_policy),
                     "load_balancing_threshold=" + str(load_balancing_threshold),
                     "refinement_policy=" + str(refinement_policy),
                     "refinement_frequency=" + str(refinement_frequency),
                     "pnmpi=${anacin_x_root}/submodules/PnMPI/build/lib/libpnmpi.so",
                     "pnmpi_lib_path=${anacin_x_root}/anacin-x/job_scripts/pnmpi_patched_libs/" ]
    if with_csmpi:
        config_lines += [ "pnmpi_conf=${anacin_x_root}/anacin-x/job_scripts/pnmpi_configs/dumpi_and_csmpi.conf",
                          "csmpi_config=./default_glibc_tellico.json" ]
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

if __name__ == "__main__":
    desc = ""
    parser = argparse.ArgumentParser( description = desc )
    parser.add_argument("repo_root_dir")
    parser.add_argument("trace_dir")
    parser.add_argument("load_balancing_policy", type=int,
                        help="Off: 0, Once per refinement step: 1, Once per refinement substep: 2")
    parser.add_argument("load_balancing_threshold", type=float,
                        help="Percentage imbalance threshold that must be met to trigger load-balancing")
    parser.add_argument("refinement_policy", type=int,
                        help="Domain-Determined Refinement: 0, Uniform Refinement: 1")
    parser.add_argument("refinement_frequency", type=int,
                        help="If using non-uniform refinement, how many time steps will occur before a mesh refinement")
    parser.add_argument("--multi_node", required=False, default=False, action="store_true")
    parser.add_argument("--with_csmpi", required=False, default=False, action="store_true")
    args = parser.parse_args()

    generate_trace_job( args.repo_root_dir,
                        args.trace_dir,
                        args.load_balancing_policy,
                        args.load_balancing_threshold,
                        args.refinement_policy,
                        args.refinement_frequency,
                        args.multi_node,
                        args.with_csmpi )




