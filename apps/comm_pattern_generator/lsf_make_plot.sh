#!/usr/bin/env bash                                                                                                                                                                                                                           

#BSUB -o make_plot-%j.out                                                                                                                                                                                                                     
#BSUB -e make_plot-%j.err                                                                                                                                                                                                                     

make_plot_script=$1
kdts_data=$2
nd_neighbor_fraction=$3

mpirun -np 1 ${make_plot_script} ${kdts_data} --nd_neighbor_fraction ${nd_neighbor_fraction}
