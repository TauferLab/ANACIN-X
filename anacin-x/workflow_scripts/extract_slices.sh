#!/usr/bin/env bash


n_procs=$1
extract_slices_script=$2
event_graph=$3
slicing_policy=$4

config_path="$(cd "$(dirname "${BASH_SOURCE[0]}")/../config" && pwd)/anacin_paths.config"
if [ -f "${config_path}" ]; then
	# shellcheck disable=SC1090
	source "${config_path}"
fi

python_bin="${python_bin:=python3}"
if [ -n "${CONDA_PREFIX:-}" ] && [ -x "${CONDA_PREFIX}/bin/python3" ]; then
	python_bin="${CONDA_PREFIX}/bin/python3"
fi

mpirun -np ${n_procs} ${python_bin} ${extract_slices_script} ${event_graph} ${slicing_policy} -o "slices"
