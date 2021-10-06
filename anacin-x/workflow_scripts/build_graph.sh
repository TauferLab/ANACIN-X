#!/usr/bin/env bash


n_procs=$1
dumpi_to_graph_bin=$2
dumpi_to_graph_config=$3
trace_dir=$4


mpirun -np ${n_procs} ${dumpi_to_graph_bin} ${dumpi_to_graph_config} ${trace_dir}
