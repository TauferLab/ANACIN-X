#!/usr/bin/env bash

system=$( hostname | sed 's/[0-9]*//g' )
#build_dir="build_${system}/"
build_dir=build

rewrite_pnmpi_submodule_urls() {
	git config --local url."https://github.com/".insteadOf git://github.com/
	git config -f .gitmodules --get-regexp '^submodule\..*\.url$' | while read -r name url
	do
		case "${url}" in
			git://github.com/*)
				git config --local "${name}" "${url/git:\/\//https://}"
				;;
		esac
	done
	git submodule sync --recursive
}

cd submodules/PnMPI
rewrite_pnmpi_submodule_urls
git submodule update --init --recursive
mkdir -p ${build_dir}
cd ${build_dir}
export CC=mpicc
export CXX=mpicxx
cmake -DCMAKE_INSTALL_PREFIX=$(pwd) -DENABLE_FORTRAN=OFF ..
make -j
make install
