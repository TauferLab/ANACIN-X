#!/usr/bin/env bash                                                                                                                                                                                                                           

#BSUB -o record_comm_pattern-%j.out                                                                                                                                                                                                           
#BSUB -e record_comm_pattern-%j.err                                                                                                                                                                                                           

n_nodes=$1
n_procs=$2
app=$3
config=$4
run_dir=$5

rempi_lib=$HOME/ReMPI/build_catalyst/lib/librempix.so
rempi_mode=0 # Recording mode                                                                                                                                                                                                                 
rempi_dir=${run_dir}/rempi
rempi_encode=4 # Use clock-delta compression                                                                                                                                                                                                  

LD_PRELOAD=${rempi_lib} REMPI_MODE=${rempi_mode} REMPI_DIR=${rempi_dir} REMPI_ENCODE=${rempi_encode} mpirun -np ${n_procs} ${app} ${config}
