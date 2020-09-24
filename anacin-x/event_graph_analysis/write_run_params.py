#!/usr/bin/env python3

#SBATCH -o write_run_params-%j.out
#SBATCH -e write_run_params-%j.err
#SBATCH -t 00:00:05

import argparse
import json


def write_run_params(pattern, n_proc, proc_placement, msg_size, nd_percentage_msg, nd_percentage_top):
    params = { "pattern" : pattern,
               "n_proc"  : n_proc,
               "proc_placement" : proc_placement,
               "msg_size" : msg_size,
               "nd_percentage_msg" : nd_percentage_msg
             }
    if nd_percentage_top is not None:
        params["nd_percentage_top"] = nd_percentage_top
    
    with open("run_params.json", "w") as outfile:
        json.dump(params, outfile)

if __name__ == "__main__":
    desc = "Write run parameters for a communication pattern to a JSON file"
    parser = argparse.ArgumentParser(description=desc)
    parser.add_argument("--pattern", help="")
    parser.add_argument("--n_proc", type=int, help="")
    parser.add_argument("--proc_placement", help="")
    parser.add_argument("--msg_size", type=int, help="")
    parser.add_argument("--nd_percentage_msg", type=float, help="")
    parser.add_argument("--nd_percentage_top", required=False, type=float, default=None, help="")
    args = parser.parse_args()
    write_run_params( args.pattern, args.n_proc, args.proc_placement, args.msg_size, args.nd_percentage_msg, args.nd_percentage_top )
