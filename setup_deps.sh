#!/usr/bin/env bash


### Get user input for variables

# Introduction
echo "Hello!  Thank you for downloading ANACIN-X."
echo
echo "Before we can start installing the software, we'll need to determine which packages you'll need."

# Set up for Environment (C Compiler, OS, and MPI)
while true; do
	read -p "Do you already have a c compiler installed? (yes/no) " user_has_comp
	case ${user_has_comp} in
		[yY] | [yY][eE][sS] ) break ;;
		[nN] | [nN][oO] ) break ;;
		* ) echo "Please respond with either yes or no: " ;;
	esac
done
while true; do
	read -p "Do you already have a version of mpi installed? (yes/no) " user_has_mpi
	        case ${user_has_mpi} in
                [yY] | [yY][eE][sS] ) while true; do
		       read -p "Which mpi installation do you have? Input is case sensitive. (openmpi, mvapich2, mpich) " user_mpi_name
		       case ${user_mpi_name} in
			       "openmpi" | "mvapich2" | "mpich" ) break ;;
			       * ) echo "Please respond with one of the listed options. Input is case sensitive. (openmpi, mvapich2, mpich) " ;;
		       esac
	       done; break ;;
                [nN] | [nN][oO] ) break ;;
                * ) echo "Please respond with either yes or no: " ;;
        esac
done
while true; do
	read -p "Which operating system are you using? Input is case sensitive. (linux x86_64, linux Power9, mac) " user_os_name
	case ${user_os_name} in
		"linux x86_64" ) os_for_conda="linux86"; break ;;
		"linux Power9" ) os_for_conda="linuxP9"; break ;;
		"mac" ) os_for_conda="mac"; break ;;
		* ) "Please respond with one of the listed options. Input is case sensitive. (linux x86_64, linux Power9, mac) " ;;
	esac
done

# Set up for Package Management
#read -p "Do you already have the Spack package manager installed? (yes/no) " user_has_spack
#if [ ${user_has_spack} = "no" ]; then
#	read -p "Where would you like to install Spack? (Press enter for the current directory.) " user_spack
#fi
while true; do
        read -p "Do you already have the Spack package manager installed? (yes/no) " user_has_spack
                case ${user_has_spack} in
                [yY] | [yY][eE][sS] ) read -p "What is the path to the directory where your installation of Spack is? " user_spack; break ;;
                [nN] | [nN][oO] ) read -p "Where would you like to install Spack? " user_spack; break ;;
                * ) echo "Please respond with either yes or no: " ;;
        esac
done
read -p "Please provide a name for a project spack environment.  It can be anything. (Press enter for default anacin_spack_env) " user_spack_name
read -p "Do you already have the Conda package manager installed? (yes/no) " user_has_conda
if [ ${user_has_conda} = "no" ]; then
	read -p "Where would you like to install Conda? (Press enter for your home directory.) " user_conda
fi



### Define variables to pass to install script

# Options of yes or no
has_spack="${user_has_spack:="yes"}"
has_conda="${user_has_conda:="yes"}"
has_c_comp="${user_has_comp:="yes"}"
has_mpi="${user_has_mpi:="yes"}"
has_ssh_key="${user_has_ssh:="yes"}"

# Options of openmpi, mvapich2, mpich
mpi_name="${user_mpi_name:="openmpi"}"

# Options of mac, linux86, linuxP9
os_for_conda="${user_os:="linux86"}"

# Needs to be correct path if on machine
conda_path="${user_conda:=""}"
spack_path="${user_spack:=""}"

# Can be anything
spack_env_name="${user_spack_name:="anacin_spack_env"}"



#bash anacin_deps.sh ${mpi_name} ${os_for_conda} ${conda_path} ${spack_path} ${spack_env_name} ${has_spack} ${has_conda} ${has_c_comp} ${has_mpi} ${has_ssh_key} 


