#!/usr/bin/env bash


n_procs=$1
extract_slices_script=$2
event_graph=$3
slicing_policy=$4

python_bin=python3
if [ -x /home/exouser/anaconda3/bin/python3 ]; then
	python_bin=/home/exouser/anaconda3/bin/python3
fi

mpirun -np ${n_procs} ${python_bin} ${extract_slices_script} ${event_graph} ${slicing_policy} -o "slices"
