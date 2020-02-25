#!/usr/bin/env bash

# Clean up previous installations
rm -rf ./submodules/*
rm -rf ./apps && mkdir apps
rm ./anacin-x/base_vars.sh

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
echo "Building NINJA Noise-Injection Agent..."
echo ${progress_delimiter}
echo
./install/install_ninja.sh
echo 
echo ${progress_delimiter}
echo "Done building NINJA Noise-Injection Agent."
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
./submodules/PnMPI/build/bin/pnmpi-patch ./submodules/csmpi/build/libcsmpi.so ./anacin-x/pnmpi/patched_libs/libcsmpi.so
./submodules/PnMPI/build/bin/pnmpi-patch ./submodules/ninja/build/libninja.so ./anacin-x/pnmpi/patched_libs/libninja.so
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

# Install applications under study
echo
echo ${progress_delimiter}
echo "Fetching non-deterministic MPI applications..."
echo ${progress_delimiter}
echo
git clone git@github.com:TauferLab/miniAMR.git ./apps/miniAMR
echo
echo ${progress_delimiter}
echo "Done fetching non-deterministic MPI applications."
echo ${progress_delimiter}
echo

echo
echo ${progress_delimiter}
echo "Building miniAMR..."
echo ${progress_delimiter}
echo
cd ./apps/miniAMR/ref && make -j && cd -
echo
echo ${progress_delimiter}
echo "Done Building miniAMR."
echo ${progress_delimiter}
echo

# Set vars for job script infrastructure
touch ./anacin-x/base_vars.sh
echo "anacin_x_root=$(pwd)" >> ./anacin-x/base_vars.sh
echo "ega_x_root=${anacin_x_root}/anacin-x/event_graph_analysis/" >> ./anacin-x/base_vars.sh

## Set up conda environment
#conda env create -f ./install/anacin-x-environment.yml
#source ./install/activate_environment.sh
