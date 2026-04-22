#!/usr/bin/env bash                                                                                                                                                                                                                           


n_procs=$1
compute_kdts_script=$2
traces_dir=$3
graph_kernel=$4
slicing_policy=$5
paths_dir=$6


source ${paths_dir}/anacin_paths.config

# graphkernels 0.2.1 may be built against a newer libstdc++ than the one
# bundled in older Conda base environments. Prefer the system runtime here.
if [ -n "${system_libstdcxx}" ] && [ -f "${system_libstdcxx}" ]; then
	export LD_PRELOAD="${system_libstdcxx}${LD_PRELOAD:+:${LD_PRELOAD}}"
fi

python_bin="${python_bin:=python3}"
if [ -n "${CONDA_PREFIX:-}" ] && [ -x "${CONDA_PREFIX}/bin/python3" ]; then
	python_bin="${CONDA_PREFIX}/bin/python3"
fi

if [ "${run_csmpi}" == "True" ]; then
	mpirun -np ${n_procs} ${python_bin} ${compute_kdts_script} ${traces_dir} ${graph_kernel} --slicing_policy ${slicing_policy} -o "kdts.pkl" --slice_dir_name "slices" -c
else
	mpirun -np ${n_procs} ${python_bin} ${compute_kdts_script} ${traces_dir} ${graph_kernel} --slicing_policy ${slicing_policy} -o "kdts.pkl" --slice_dir_name "slices"
fi
