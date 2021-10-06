#!/usr/bin/env bash

#BSUB -o comm_pattern-%j.out
#BSUB -e comm_pattern-%j.err

#system=$(hostname | sed 's/[0-9]*//g')

n_procs=$1
app=$2
config=$3
n_nodes=${n_procs}

source ./example_paths.config

# Define tool stack
#anacin_x_root=$HOME/ANACIN-X
#pnmpi=${anacin_x_root}/submodules/PnMPI/build_${system}/lib/libpnmpi.so
#pnmpi_lib_path=${anacin_x_root}/anacin-x//pnmpi/patched_libs/
#pnmpi_conf=${anacin_x_root}/anacin-x/pnmpi/configs/dumpi.conf

LD_PRELOAD=${pnmpi} PNMPI_LIB_PATH=${pnmpi_lib_path} PNMPI_CONF=${pnmpi_conf} mpirun -np ${n_procs} -pernode ${app} ${config}
