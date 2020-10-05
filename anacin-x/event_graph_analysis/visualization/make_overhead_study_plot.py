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
#matplotlib.use('TkAgg')
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


def get_scale_from_scale_dir( sd ):
    base_name = os.path.basename( os.path.realpath(sd) )
    scale = int(base_name.split("_")[-1])
    return scale

def get_cfg_from_cfg_dir( cfg_dir ):
    base_name = os.path.basename( os.path.realpath(cfg_dir) )
    return base_name

def get_scale_to_cfg_dirs( trace_dir, scales ):
    scale_dirs = sorted(glob.glob(trace_dir+"/nprocs_*/"))
    scale_to_scale_dirs = { get_scale_from_scale_dir(sd):sd for sd in scale_dirs }
    selected_scale_to_scale_dirs = { np:scale_to_scale_dirs[np] for np in scales }
    scale_to_cfg_dirs = { np:{ get_cfg_from_cfg_dir(cfg_dir):cfg_dir for cfg_dir in glob.glob(sd+"/*/") } for np,sd in selected_scale_to_scale_dirs.items() }
    return scale_to_cfg_dirs

def get_scale_to_elapsed_times( scale_to_cfg_dirs ):
    scale_to_run_dirs =  { np : { cfg : sorted(glob.glob(cfg_dir+"/run*/")) for cfg,cfg_dir in cfg_dirs.items() } for np,cfg_dirs in scale_to_cfg_dirs.items() }
    scale_to_elapsed_times = { np : { cfg : get_elapsed_times(run_dirs) for cfg,run_dirs in cfg_dirs.items() } for np,cfg_dirs in scale_to_run_dirs.items() }
    return scale_to_elapsed_times

def get_scale_to_overheads( scale_to_elapsed_times ):
    scale_to_overheads = {}
    for np in scale_to_elapsed_times:
        cfg_to_elapsed_times = scale_to_elapsed_times[np]
        n_run_indices_set = set()
        for cfg, run_to_time in cfg_to_elapsed_times.items():
            n_run_indices_set.add( len(run_to_time.keys()) )
        assert(len(n_run_indices_set) == 1 )
        run_indices = sorted(run_to_time.keys())
        cfg_to_overheads = {}
        for idx in run_indices:
            for cfg in cfg_to_elapsed_times.keys():
                if cfg == "base":
                    overhead = 1.0
                elif cfg == "dumpi":
                    overhead = cfg_to_elapsed_times["dumpi"][idx] / cfg_to_elapsed_times["base"][idx]
                elif cfg == "dumpi_csmpi":
                    overhead = cfg_to_elapsed_times["dumpi_csmpi"][idx] / cfg_to_elapsed_times["base"][idx]
                if cfg not in cfg_to_overheads:
                    cfg_to_overheads[cfg] = [ overhead ]
                else:
                    cfg_to_overheads[cfg].append( overhead )
        scale_to_overheads[np] = cfg_to_overheads
    return scale_to_overheads

def main( trace_dir, scales ):
    scale_to_cfg_dirs = get_scale_to_cfg_dirs( trace_dir, scales )
    scale_to_elapsed_times = get_scale_to_elapsed_times( scale_to_cfg_dirs )
    scale_to_overheads = get_scale_to_overheads( scale_to_elapsed_times )
    
    figure_size = (16, 9)
    fig, ax = plt.subplots(figsize=figure_size)
    box_width = 0.8
    cfg_to_color = { "dumpi" : "b", "dumpi_csmpi" : "r" }
    flier_props = { "marker" : "+", "markersize" : 4 }
    cfgs_to_plot = [ "dumpi", "dumpi_csmpi" ]
    cfg_to_label = { "dumpi" : "DUMPI", "dumpi_csmpi" : "DUMPI + CSMPI" }

    curr_box_position = 0
    y_max = 0
    all_bps = []
    all_labels = []
    have_legend_data = False
    for np in scales:
        for cfg in cfgs_to_plot:
            box_data = scale_to_overheads[np][cfg]
            box_data = [ y*100 for y in box_data ]
            y_max = max(y_max, max(box_data))
            box_position = [ curr_box_position ]
            box_props = { "alpha" : 0.5, "facecolor" : cfg_to_color[cfg] }
            bp = ax.boxplot( box_data,
                                positions=box_position,
                                widths=box_width,
                                patch_artist=True,
                                showfliers=True,
                                boxprops=box_props,
                                flierprops=flier_props)
            if not have_legend_data:
                all_bps.append(bp)
                all_labels.append( cfg_to_label[cfg] )
            curr_box_position += 1
        have_legend_data = True
        curr_box_position += 1
    # Configure x-axis
    n_configs = len(cfgs_to_plot)
    x_ticks = [ 0.5 + i*(n_configs+1) for i in range(n_configs) ]
    x_tick_labels = sorted( scales )
    x_axis_label = "Scale (# MPI Processes)"
    ax.set_xticks( x_ticks )
    ax.set_xticklabels( x_tick_labels )
    ax.set_xlabel(x_axis_label)
    # Configure y-axis
    y_axis_label = "Overhead (% base runtime)"
    ax.set_ylim(100, y_max * 1.01 )
    ax.set_ylabel(y_axis_label)
    # Configure legend
    ax.legend([bp["boxes"][0] for bp in all_bps], all_labels, loc="best")
    # Persist
    plt.savefig("overhead_study.png",
                bbox_inches="tight",
                pad_inches=0.25)

if __name__ == "__main__":
    desc = ""
    parser = argparse.ArgumentParser(description=desc)
    parser.add_argument("trace_dir", 
                        help="")
    parser.add_argument("-s", "--scales", nargs="+", type=int,
                        help="")
    args = parser.parse_args()
    main( args.trace_dir, args.scales )
