#!/usr/bin/env bash

system=$( hostname | sed 's/[0-9]*//g' )
#build_dir=build_${system}
build_dir=build

cd submodules/sst-dumpi
mkdir -p ${build_dir}
export CC=mpicc
export CXX=mpicxx
export F77=mpifort
export F90=mpifort
export FC=mpifort
$(pwd)/bootstrap.sh
$(pwd)/configure --prefix=$(pwd)/${build_dir} --enable-libdumpi --enable-libundumpi --disable-f77 --disable-f90
make -j
make install
