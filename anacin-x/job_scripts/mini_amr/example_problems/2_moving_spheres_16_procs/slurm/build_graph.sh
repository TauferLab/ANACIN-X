#!/usr/bin/env bash

#SBATCH -o build_graph-%j.out
#SBATCH -e build_graph-%j.err

dumpi_to_graph_bin=$1
dumpi_to_graph_config=$2
trace_dir=$3


srun -N1 -n16 ${dumpi_to_graph_bin} ${dumpi_to_graph_config} ${trace_dir}
