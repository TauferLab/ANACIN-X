#!/usr/bin/env bash

system=$( hostname | sed 's/[0-9]*//g' )
#build_dir="build_${system}/"
build_dir=build/
if [ ${system} == "quartz" ]; then
    build_dir="./build_quartz"
elif [ ${system} == "catalyst" ]; then
    build_dir="./build_catalyst"
fi

rm -rf ${build_dir} && mkdir ${build_dir}
cd ${build_dir}
export CC=mpicc
export CXX=mpicxx
cmake -D CMAKE_BUILD_TYPE=Debug .. && make -j

