#!/usr/bin/env bash

#SBATCH -o mini_amr_%j.out
#SBATCH -e mini_amr_%j.err

mini_amr_bin=$1
load_balancing_policy=$2
load_balancing_threshold=$3
refinement_policy=$4
refinement_frequency=$5

LD_PRELOAD=${pnmpi} PNMPI_LIB_PATH=${pnmpi_lib_path} PNMPI_CONF=${pnmpi_conf} srun -N1 -n16 ${mini_amr_bin} \
    --num_refine 4 \
    --max_blocks 4000 \
    --init_x 1 \
    --init_y 1 \
    --init_z 1 \
    --npx 4 \
    --npy 2 \
    --npz 2 \
    --nx 8 \
    --ny 8 \
    --nz 8 \
    --num_objects 2 \
    --object 2 0 -1.10 -1.10 -1.10 0.030 0.030 0.030 1.5 1.5 1.5 0.0 0.0 0.0 \
    --object 2 0 0.5 0.5 1.76 0.0 0.0 -0.025 0.75 0.75 0.75 0.0 0.0 0.0 \
    --num_tsteps 100 \
    --checksum_freq 4 \
    --stages_per_ts 16 \
    --lb_opt ${load_balancing_policy} \
    --inbalance ${lb_balancing_threshold} \
    --uniform_refine ${refinement_policy} \
    --refine_freq ${refinement_frequency}
