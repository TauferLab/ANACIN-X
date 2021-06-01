#!/usr/bin/env bash

# Clean up previous installations
rm -rf ./submodules/*

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
git submodule update --init --recursive
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

# Set vars for job script infrastructure
anacin_x_root=$(pwd)
sed -i "s#anacin_x_root= #anacin_x_root=${anacin_x_root}#" ./apps/comm_pattern_generator/comm_pattern_config.config

sed -i "s#anacin_x_root= #anacin_x_root=${anacin_x_root}#" ./apps/comm_pattern_generator/unscheduled/example_paths_unscheduled.config
sed -i "s#anacin_x_root= #anacin_x_root=${anacin_x_root}#" ./apps/comm_pattern_generator/slurm/example_paths_slurm.config
sed -i "s#anacin_x_root= #anacin_x_root=${anacin_x_root}#" ./apps/comm_pattern_generator/lsf/example_paths_lsf.config
## Set up conda environment
#conda env create -f ./install/anacin-x-environment.yml
#source ./install/activate_environment.sh
