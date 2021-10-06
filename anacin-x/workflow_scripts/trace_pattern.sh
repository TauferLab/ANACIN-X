#!/usr/bin/env bash

n_procs=$1
app=$2
config=$3
paths_dir=$4

source ${paths_dir}/anacin_paths.config

LD_PRELOAD=${pnmpi} PNMPI_LIB_PATH=${pnmpi_lib_path} PNMPI_CONF=${pnmpi_conf} mpirun -np ${n_procs} ${app} ${config}
