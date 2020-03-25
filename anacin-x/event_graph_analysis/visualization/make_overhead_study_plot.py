#!/usr/bin/env python3

#SBATCH -n 1
#SBATCH -n 1
#SBATCH -t 01:00:00
#SBATCH -o make_overhead_study_plot-%j.out
#SBATCH -e make_overhead_study_plot-%j.err

import argparse
import os
import glob

import numpy as np

import matplotlib
matplotlib.use('TkAgg')
import matplotlib.pyplot as plt

import pprint

# /p/lscratchh/chapp1/mini_amr/system_catalyst/nprocs_16_2_moving_spheres/overhead_study/base/run_002/
def get_run_idx_from_run_dir( rd ):
    base_name = os.path.basename( os.path.realpath(rd) )
    run_idx = int(base_name.split("_")[-1])
    return run_idx

def get_elapsed_times( run_dirs ):
    run_idx_to_elapsed_time = {}
    for rd in run_dirs:
        log_path = rd + "/elapsed_time.txt"
        run_idx = get_run_idx_from_run_dir( rd )
        try:
            assert( os.path.isfile( log_path ) )
            with open( log_path, "r" ) as infile:
                lines = infile.readlines()
                assert(len(lines)==1)
                elapsed_time = float(lines[0])
                run_idx_to_elapsed_time[ run_idx ] = elapsed_time
        except:
            run_idx_to_elapsed_time[ run_idx ] = None
    return run_idx_to_elapsed_time

def main( trace_dir, mode ):
    base_runs = sorted(glob.glob( trace_dir + "/base/run*/" ))
    dumpi_runs = sorted(glob.glob( trace_dir + "/dumpi/run*/" ))
    dumpi_csmpi_runs = sorted(glob.glob( trace_dir + "/dumpi_csmpi/run*/" ))
    run_idx_to_base_elapsed_times = get_elapsed_times( base_runs )
    run_idx_to_dumpi_elapsed_times = get_elapsed_times( dumpi_runs )
    run_idx_to_dumpi_csmpi_elapsed_times = get_elapsed_times( dumpi_csmpi_runs )
    cfg_to_overheads = {}
    for idx in run_idx_to_base_elapsed_times.keys():
        for cfg in [ "base", "dumpi", "dumpi_csmpi" ]:
            if cfg == "base":
                overhead = 1.0
            elif cfg == "dumpi":
                overhead = run_idx_to_dumpi_elapsed_times[idx] / run_idx_to_base_elapsed_times[idx]
            elif cfg == "dumpi_csmpi":
                overhead = run_idx_to_dumpi_csmpi_elapsed_times[idx] / run_idx_to_base_elapsed_times[idx]
            if cfg not in cfg_to_overheads:
                cfg_to_overheads[cfg] = [ overhead ]
            else:
                cfg_to_overheads[cfg].append( overhead )

    cfg_to_elapsed_times = { "base" : run_idx_to_base_elapsed_times.values(),
                             "dumpi" : run_idx_to_dumpi_elapsed_times.values(),
                             "dumpi_csmpi" : run_idx_to_dumpi_csmpi_elapsed_times.values() }
    figure_size = (16, 9)
    fig, ax = plt.subplots(figsize=figure_size)
    configs = ["dumpi", "dumpi_csmpi"]
    box_position = [0]
    box_width = 1.0
    cfg_to_color = { "base" : "g", "dumpi" : "b", "dumpi_csmpi" : "r" }
    flier_props = { "marker" : "+", "markersize" : 4 }
    for cfg in configs:
        if mode == "overhead":
            box_data = list(filter(lambda x: x is not None, cfg_to_overheads[cfg]))
        elif mode == "raw":
            box_data = list(filter(lambda x: x is not None, cfg_to_elapsed_times[cfg]))

        box_props = { "alpha" : 0.5, "facecolor" : cfg_to_color[cfg] }
        ax.boxplot( box_data,
                    positions=box_position,
                    patch_artist=True,
                    showfliers=True,
                    boxprops=box_props,
                    flierprops=flier_props )
        box_position[0] += 1
    # Configure x-axis
    x_ticks = range(len(configs))
    x_tick_labels = configs
    x_axis_label = "Tracing Configuration"
    ax.set_xticks( x_ticks )
    ax.set_xticklabels( x_tick_labels )
    ax.set_xlabel(x_axis_label)
    #ax.set_xlim(-1, len(x_ticks)+1)
    # Configure y-axis
    if mode == "overhead":
        y_max = max( [ max(y) for y in cfg_to_overheads.values() ] )
        y_axis_label = "Overhead (% base runtime)"
        ax.set_ylim(1.0, y_max * 1.01 )
    elif mode == "raw":
        y_max = max( [ max(y) for y in cfg_to_elapsed_times.values() ] )
        y_axis_label = "Elapsed Time (s)"
        ax.set_ylim(0, y_max * 1.05)
    ax.set_ylabel(y_axis_label)
    # Persist
    plt.savefig("overhead_study.png",
                bbox_inches="tight",
                pad_inches=0.25)

if __name__ == "__main__":
    desc = ""
    parser = argparse.ArgumentParser(description=desc)
    parser.add_argument("trace_dir", 
                        help="")
    parser.add_argument("-m", "--mode", required=False, default="overhead",
                        help="")
    args = parser.parse_args()
    main( args.trace_dir, args.mode )
