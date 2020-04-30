#!/usr/bin/env bash

#kernel="vertex_histogram"
kernels="$@"

base_dir="/p/lscratchh/chapp1/thesis_results/comm_patterns/amg2013/system_catalyst/n_procs_21/proc_placement_pack/msg_size_1/"
run_dir_depth=1
max_run_idx=1
cache="./test_kernel_matrices.pkl"
kernel_matrices_out="./test_kernel_matrices.pkl"
run_params_out="./test_run_params.pkl"

echo "Computing kernel matrices"
./graph_kernels.py --base_dir ${base_dir} \
                   --run_dir_depth ${run_dir_depth} \
                   --kernels ${kernels} \
                   --max_run_idx ${max_run_idx} \
                   --kernel_matrices_cache ${cache} \
                   --kernel_matrices_output ${kernel_matrices_out} \
                   --run_params_output ${run_params_out} \
                   --wl_iters 2 4 8 \
                   --graphlet_sampling_dims 3 5 \
                   --graphlet_sampling_counts 10 100 


#echo "Building SVR models"
#./models.py --kernel_matrices ${kernel_matrices_out} \
#            --graph_labels ${run_params_out} \
#            --predict "nd_percentage_msg" \
#            --output "model.pkl" \
#            --n_folds 10 \
#            --n_repeats 10

