#!/usr/bin/env bash

cd submodules/Pluto
build_dir=build

export CC=mpicc
export CXX=mpicxx
rm -rf "$(pwd)/${build_dir}"
mkdir -p "$(pwd)/${build_dir}"
cd "${build_dir}"
cmake ..
make -j
