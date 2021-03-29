#!/usr/bin/env bash


### Define variables to pass to install script

# Options of yes or no
has_spack="${user_has_spack:="yes"}"
has_conda="${user_has_conda:="yes"}"
has_c_comp="${user_has_comp:="yes"}"
has_mpi="${user_has_mpi:="yes"}"
has_ssh_key="${user_has_ssh:="yes"}"

# Options of openmpi, mvapich2, mpich
mpi_name="${user_mpi_name:="openmpi"}"

# Options of mac, win64, win32, linux86, linuxP9
os_for_conda="${user_os:="linux86"}"

# Needs to be correct path if on machine
conda_path="${user_conda:=""}"
spack_path="${user_spack:=""}"

# Can be anything
spack_env_name="${user_spack_name:="anacin_spack_env"}"



bash anacin_deps.sh ${mpi_name} ${os_for_conda} ${conda_path} ${spack_path} ${spack_env_name} ${has_spack} ${has_conda} ${has_c_comp} ${has_mpi} ${has_ssh_key} 


