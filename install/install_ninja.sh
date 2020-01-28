#!/usr/bin/env bash

cd submodules/ninja
mkdir -p build
$(pwd)/autogen.sh
$(pwd)/configure --prefix=$(pwd)/build
make -j
make install
