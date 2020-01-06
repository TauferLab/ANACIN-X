#!/usr/bin/env bash

cd submodules/sst-dumpi
mkdir -p build
export CC=mpicc
export CXX=mpicxx
$(pwd)/bootstrap.sh
$(pwd)/configure --prefix=$(pwd)/build --enable-libdumpi 
make -j
make install
