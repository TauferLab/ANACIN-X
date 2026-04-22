#!/usr/bin/env bash

while [ -n "$1" ]; do
	case "$1" in
		-c)  run_csmpi="True"; shift ;;
		-sc) scheduler=$2; shift; shift ;;
	esac
done

rewrite_pnmpi_submodule_urls() {
	git -C ./submodules/PnMPI config --local url."https://github.com/".insteadOf git://github.com/
	sed -i 's#git://github.com/#https://github.com/#g' ./submodules/PnMPI/.gitmodules
	git config -f ./submodules/PnMPI/.gitmodules --get-regexp '^submodule\..*\.url$' | while read -r name url
	do
		case "${url}" in
			https://github.com/*)
				git -C ./submodules/PnMPI config --local "${name}" "${url}"
				;;
		esac
	done
	git -C ./submodules/PnMPI submodule sync --recursive
}

apply_submodule_compatibility_patches() {
	csmpi_header="./submodules/CSMPI/include/csmpi/callstack.hpp"
	dumpi_comm_manager="./submodules/dumpi_to_graph/src/CommunicatorManager.cpp"

	if [ -f "${csmpi_header}" ]; then
		if ! grep -q '^#include <cstdint>$' "${csmpi_header}"; then
			sed -i '/#include "boost\/functional\/hash.hpp"/i #include <cstdint>' "${csmpi_header}"
		fi
		if ! grep -q '^#include <vector>$' "${csmpi_header}"; then
			sed -i '/#include "boost\/functional\/hash.hpp"/i #include <vector>' "${csmpi_header}"
		fi
	fi

	if [ -f "${dumpi_comm_manager}" ]; then
		if ! grep -q '^#include <set>$' "${dumpi_comm_manager}"; then
			sed -i '/#include <iostream>/a #include <set>' "${dumpi_comm_manager}"
		fi
	fi
}

# Clean up previous installations
rm -rf ./submodules/*

run_csmpi="${run_csmpi:="False"}"
scheduler="${scheduler:="unscheduled"}"
repo_root="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
local_config_path="${repo_root}/anacin-x/config/anacin_paths.local.config"
n_columns=$(stty size | awk '{print $2}')
progress_delimiter=""
for i in `seq 1 ${n_columns}`;
do
    progress_delimiter+="-"
done

# First, get all relevant submodules
echo
echo ${progress_delimiter}
echo "Fetching submodules..."
echo ${progress_delimiter}
echo
git config --local url."https://github.com/".insteadOf git://github.com/
git submodule update --init
rewrite_pnmpi_submodule_urls
git submodule update --init --recursive
git submodule sync --recursive
git submodule update --init --remote submodules/Pluto submodules/CSMPI submodules/dumpi_to_graph
apply_submodule_compatibility_patches
echo
echo ${progress_delimiter}
echo "Done fetching submodules."
echo ${progress_delimiter}
echo

# Build tracing infrastructure (DUMPI, CSMPI, NINJA, PnMPI)
echo
echo ${progress_delimiter}
echo "Building SST-DUMPI..."
echo ${progress_delimiter}
echo
./install/install_dumpi.sh
echo 
echo ${progress_delimiter}
echo "Done building SST-DUMPI."
echo ${progress_delimiter}
echo

echo
echo ${progress_delimiter}
echo "Building Pluto..."
echo ${progress_delimiter}
echo
./install/install_pluto.sh
echo 
echo ${progress_delimiter}
echo "Done building Pluto."
echo ${progress_delimiter}
echo

if [ "${run_csmpi}" == "True" ]; then
echo
echo ${progress_delimiter}
echo "Building CSMPI..."
echo ${progress_delimiter}
echo
./install/install_csmpi.sh
echo 
echo ${progress_delimiter}
echo "Done building CSMPI."
echo ${progress_delimiter}
echo
fi

echo
echo ${progress_delimiter}
echo "Building PnMPI..."
echo ${progress_delimiter}
echo
./install/install_pnmpi.sh
echo 
echo ${progress_delimiter}
echo "Done building PnMPI."
echo ${progress_delimiter}
echo

# Patch tracing libraries for use with PnMPI
echo
echo ${progress_delimiter}
echo "Patching tracing libraries for use with PnMPI..."
echo ${progress_delimiter}
echo 
./submodules/PnMPI/build/bin/pnmpi-patch ./submodules/sst-dumpi/build/lib/libdumpi.so ./anacin-x/pnmpi/patched_libs/libdumpi.so
./submodules/PnMPI/build/bin/pnmpi-patch ./submodules/Pluto/build/libpluto.so ./anacin-x/pnmpi/patched_libs/libpluto.so
if [ "${run_csmpi}" == "True" ]; then
./submodules/PnMPI/build/bin/pnmpi-patch ./submodules/CSMPI/build/libcsmpi.so ./anacin-x/pnmpi/patched_libs/libcsmpi.so
fi
echo
echo ${progress_delimiter}
echo "Done patching tracing libraries for use with PnMPI..."
echo ${progress_delimiter}
echo

# Build dumpi_to_graph
echo
echo ${progress_delimiter}
echo "Building graph constructor..."
echo ${progress_delimiter}
echo
./install/install_dumpi_to_graph.sh
echo 
echo ${progress_delimiter}
echo "Done building graph constructor."
echo ${progress_delimiter}
echo

# Build Comm Pattern Generator
echo
echo ${progress_delimiter}
echo "Building Comm Pattern Generator..."
echo ${progress_delimiter}
echo
./install/install_comm_pattern_generator.sh
echo
echo ${progress_delimiter}
echo "Done Building Comm Pattern Generator."
echo ${progress_delimiter}
echo

# Persist local installation-specific settings without hardcoding them in the
# tracked repo config file.
python_bin="${ANACIN_X_PYTHON:-}"
if [ -n "${CONDA_PREFIX:-}" ] && [ -d "${CONDA_PREFIX}/bin" ]; then
	export PATH="${CONDA_PREFIX}/bin:${PATH}"
fi
if [ -z "${python_bin}" ] && [ -n "${CONDA_PREFIX:-}" ] && [ -x "${CONDA_PREFIX}/bin/python" ]; then
	python_bin="${CONDA_PREFIX}/bin/python"
fi
if [ -z "${python_bin}" ] && [ -n "${CONDA_PREFIX:-}" ] && [ -x "${CONDA_PREFIX}/bin/python3" ]; then
	python_bin="${CONDA_PREFIX}/bin/python3"
fi
if [ -z "${python_bin}" ]; then
	python_bin="$(command -v python || command -v python3)"
fi

system_libstdcxx=""
for candidate in \
	/usr/lib/x86_64-linux-gnu/libstdc++.so.6 \
	/usr/lib64/libstdc++.so.6 \
	/usr/lib/libstdc++.so.6; do
	if [ -f "${candidate}" ]; then
		system_libstdcxx="${candidate}"
		break
	fi
done

cat > "${local_config_path}" <<EOF
run_csmpi=${run_csmpi}
python_bin=${python_bin}
system_libstdcxx=${system_libstdcxx}
EOF
## Set up conda environment
#conda env create -f ./install/anacin-x-environment.yml
#source ./install/activate_environment.sh
