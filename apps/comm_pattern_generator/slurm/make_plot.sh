#!/usr/bin/env bash

#SBATCH -o make_plot-%j.out
#SBATCH -e make_plot-%j.err

make_plot_script=$1
kdts_data=$2
nd_neighbor_fraction=$3

srun -N1 -n1 ${make_plot_script} ${kdts_data} --nd_neighbor_fraction ${nd_neighbor_fraction}

