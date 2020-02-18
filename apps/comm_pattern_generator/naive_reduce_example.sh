#!/usr/bin/env bash

anacin_x_root=$HOME/repos/ANACIN-X
pnmpi=${anacin_x_root}/submodules/PnMPI/build/lib/libpnmpi.so
pnmpi_lib_path=${anacin_x_root}/anacin-x/job_scripts/pnmpi_patched_libs/

pnmpi_conf=${anacin_x_root}/anacin-x/job_scripts/pnmpi_configs/dumpi.conf
#pnmpi_conf=${anacin_x_root}/anacin-x/job_scripts/pnmpi_configs/dumpi_ninja.conf

app=${anacin_x_root}/apps/comm_pattern_generator/build/comm_pattern_generator
config=${anacin_x_root}/apps/comm_pattern_generator/config/naive_reduce_example_msg_size_1.json

n_procs=11

LD_PRELOAD=${pnmpi} PNMPI_LIB_PATH=${pnmpi_lib_path} PNMPI_CONF=${pnmpi_conf} mpirun -np ${n_procs} ${app} ${config}
