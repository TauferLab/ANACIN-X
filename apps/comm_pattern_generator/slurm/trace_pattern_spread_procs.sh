#!/usr/bin/env bash

#SBATCH -o comm_pattern-%j.out
#SBATCH -e comm_pattern-%j.err

#system=$(hostname | sed 's/[0-9]*//g')
source ./example_paths.config

n_procs=$1
app=$2
config=$3
n_nodes=${n_procs}

# Define tool stack
#anacin_x_root=$HOME/Src_ANACIN-X
#pnmpi=${anacin_x_root}/submodules/PnMPI/build_${system}/lib/libpnmpi.so
#pnmpi_lib_path=${anacin_x_root}/anacin-x//pnmpi/patched_libs/
#pnmpi_conf=${anacin_x_root}/anacin-x/pnmpi/configs/dumpi.conf

LD_PRELOAD=${pnmpi} PNMPI_LIB_PATH=${pnmpi_lib_path} PNMPI_CONF=${pnmpi_conf} srun -N${n_nodes} -n${n_procs} --ntasks-per-node=1 ${app} ${config}
