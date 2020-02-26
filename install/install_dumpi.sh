#!/usr/bin/env bash

system=$( hostname | sed 's/[0-9]*//g' )
build_dir=build/${system}

cd submodules/sst-dumpi
mkdir -p ${build_dir}
export CC=mpicc
export CXX=mpicxx
$(pwd)/bootstrap.sh
$(pwd)/configure --prefix=$(pwd)/${build_dir} --enable-libdumpi 
make -j
make install
