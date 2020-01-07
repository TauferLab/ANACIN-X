#!/usr/bin/env bash

rm -rf ./submodules/*

n_columns=$(stty size | awk '{print $2}')
progress_delimiter=""
for i in `seq 1 ${n_columns}`;
do
    progress_delimiter+="-"
done

# First, get all relevant submodules
echo ${progress_delimiter}
echo "fetching submodules..."
echo ${progress_delimiter}
echo
git submodule update --init --recursive
echo
echo ${progress_delimiter}
echo "Done fetching submodules."
echo ${progress_delimiter}

# Build tracing infrastructure (DUMPI, CSMPI, PnMPI)
echo ${progress_delimiter}
echo "Building SST-DUMPI..."
echo ${progress_delimiter}
echo
./install/install_dumpi.sh
echo 
echo ${progress_delimiter}
echo "Done building SST-DUMPI."
echo ${progress_delimiter}

echo ${progress_delimiter}
echo "Building CSMPI..."
echo ${progress_delimiter}
echo
./install/install_csmpi.sh
echo 
echo ${progress_delimiter}
echo "Done building CSMPI."
echo ${progress_delimiter}

echo ${progress_delimiter}
echo "Building PnMPI..."
echo ${progress_delimiter}
echo
./install/install_pnmpi.sh
echo 
echo ${progress_delimiter}
echo "Done building PnMPI."
echo ${progress_delimiter}

# Patch tracing libraries for use with PnMPI
echo ${progress_delimiter}
echo "Patching tracing libraries for use with PnMPI..."
echo ${progress_delimiter}
echo 
mkdir -p ./anacin-x/tracing/pnmpi_patched_libs
./submodules/PnMPI/build/bin/pnmpi-patch ./submodules/sst-dumpi/build/lib/libdumpi.so ./anacin-x/tracing/pnmpi_patched_libs/libdumpi.so
./submodules/PnMPI/build/bin/pnmpi-patch ./submodules/csmpi/build/libcsmpi.so ./anacin-x/tracing/pnmpi_patched_libs/libcsmpi.so
echo
echo ${progress_delimiter}
echo "Done patching tracing libraries for use with PnMPI..."
echo ${progress_delimiter}

# Build dumpi_to_graph
echo ${progress_delimiter}
echo "Building graph constructor..."
echo ${progress_delimiter}
echo
./install/install_dumpi_to_graph.sh
echo 
echo ${progress_delimiter}
echo "Done building graph constructor."
echo ${progress_delimiter}

