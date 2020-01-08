#!/usr/bin/env bash

#SBATCH -o build_graph_%j.out
#SBATCH -e build_graph_%j.err

trace_dir=$1
dumpi_to_graph_bin=$2
dumpi_to_graph_config=$3

srun -N1 -n16 ${dumpi_to_graph_bin} ${dumpi_to_graph_config} ${trace_dir}
