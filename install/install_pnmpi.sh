#!/usr/bin/env bash

system=$( hostname | sed 's/[0-9]*//g' )
build_dir=build/${system}

cd submodules/PnMPI
git submodule update --init --recursive
mkdir -p ${build_dir}
cd ${build_dir}
export CC=mpicc
export CXX=mpicxx
cmake -DCMAKE_INSTALL_PREFIX=$(pwd) -DENABLE_FORTRAN=OFF ..
make -j
make install
