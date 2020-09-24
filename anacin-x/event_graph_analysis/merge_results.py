#!/usr/bin/env python3

import argparse
import pickle as pkl


def main(base_kdef_to_results_path, base_kernel_matrices_path, new_kdef_to_results_path, new_kernel_matrices_path):
    with open(base_kdef_to_results_path, "rb") as infile:
        base_kdef_to_results = pkl.load(infile)

    with open(new_kdef_to_results_path, "rb") as infile:
        new_kdef_to_results = pkl.load(infile)

    for k,v in new_kdef_to_results.items():
        if k not in base_kdef_to_results:
            base_kdef_to_results[k] = v

    with open(base_kdef_to_results_path, "wb") as outfile:
        pkl.dump(base_kdef_to_results, outfile, protocol=0)
    
    with open(base_kernel_matrices_path, "rb") as infile:
        base_kernel_matrices = pkl.load(infile)

    with open(new_kernel_matrices_path, "rb") as infile:
        new_kernel_matrices = pkl.load(infile)

    for k,v in new_kernel_matrices.items():
        if k not in base_kernel_matrices:
            base_kernel_matrices[k] = v

    with open(base_kernel_matrices_path, "wb") as outfile:
        pkl.dump(base_kernel_matrices, outfile, protocol=0)
        

if __name__ == "__main__":
    desc = ""
    parser = argparse.ArgumentParser(description=desc)
    parser.add_argument("base_kdef_to_results", help="")
    parser.add_argument("base_kernel_matrices", help="")
    parser.add_argument("new_kdef_to_results", help="")
    parser.add_argument("new_kernel_matrices", help="")
    args = parser.parse_args()

    main(args.base_kdef_to_results,
         args.base_kernel_matrices,
         args.new_kdef_to_results,
         args.new_kernel_matrices)
