#!/usr/bin/env bash

cd submodules/PnMPI
git submodule update --init --recursive
mkdir -p build
cd build
export CC=mpicc
export CXX=mpicxx
cmake -DCMAKE_INSTALL_PREFIX=$(pwd) -DENABLE_FORTRAN=OFF ..
make -j
make install
