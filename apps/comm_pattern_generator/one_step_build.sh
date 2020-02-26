#!/usr/bin/env bash

rm -rf ./build && mkdir build
cd build
export CC=mpicc
export CXX=mpicxx
cmake .. && make -j

