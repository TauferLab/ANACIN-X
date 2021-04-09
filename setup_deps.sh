#!/usr/bin/env bash


### Get user input for variables

# Introduction
echo "Hello!  Thank you for downloading ANACIN-X."
echo
echo "Before we can start installing the software, we'll need to determine which packages you'll need."

# Verify user has ssh set up.s
while true; do
	read -p "Do you have an ssh key pair set up in github? (yes/no) " user_has_ssh
	case ${user_has_ssh} in
                [yY] | [yY][eE][sS] ) has_ssh_key="yes"; break ;;
                [nN] | [nN][oO] ) echo "You will need to set up an ssh key with github prior to installation."
			echo "Please review instructions for how to do so at https://docs.github.com/en/github/authenticating-to-github/generating-a-new-ssh-key-and-adding-it-to-the-ssh-agent"
			echo "Please see https://github.com/TauferLab/Src_ANACIN-X for a full list of necessary installs."
			exit ;;
                * ) echo "Please respond with either yes or no: " ;;
	esac
done

# Set up for Environment (C Compiler, OS, and MPI)
while true; do
	read -p "Do you already have a c compiler installed? (yes/no) " user_has_comp
	case ${user_has_comp} in
		[yY] | [yY][eE][sS] ) has_c_comp="yes"; break ;;
		[nN] | [nN][oO] ) has_c_comp="no"
			echo "Please install a version of gcc before continuing"
			echo "Please see https://github.com/TauferLab/Src_ANACIN-X for a full list of necessary installs."
			exit ;;
		* ) echo "Please respond with either yes or no: " ;;
	esac
done
while true; do
	read -p "Do you already have a version of mpi installed? (yes/no) " user_has_mpi
	case ${user_has_mpi} in
#                [yY] | [yY][eE][sS] ) has_mpi="yes"; while true; do
#		       read -p "Which mpi installation do you have? Input is case sensitive. (openmpi, mvapich2, mpich) " user_mpi_name
#		       case ${user_mpi_name} in
#			       "openmpi" | "mvapich2" | "mpich" ) break ;;
#			       * ) echo "Please respond with one of the listed options. Input is case sensitive. (openmpi, mvapich2, mpich) " ;;
#		       esac
#	         done; break ;;
		[yY] | [yY][eE][sS] ) has_mpi="yes"; break ;;
		[nN] | [nN][oO] ) has_mpi="no"; break ;;
                * ) echo "Please respond with either yes or no: " ;;
        esac
done
#while true; do
#	read -p "Which operating system are you using? Input is case sensitive. (linux x86_64, linux Power9, mac) " user_os_name
#	case ${user_os_name} in
#		"linux x86_64" ) os_for_conda="linux86"; break ;;
#		"linux Power9" ) os_for_conda="linuxP9"; break ;;
#		"mac" ) os_for_conda="mac"; break ;;
#		* ) "Please respond with one of the listed options. Input is case sensitive. (linux x86_64, linux Power9, mac) " ;;
#	esac
#done

# Set up for Package Management
while true; do
        read -p "Do you already have the Spack package manager installed? (yes/no) " user_has_spack
        case ${user_has_spack} in
        	[yY] | [yY][eE][sS] ) has_spack="yes"; break ;;
		[nN] | [nN][oO] ) echo "You will need to install Spack prior to installation."
			echo "Please review instructions for spack installation at https://spack.readthedocs.io/en/latest/getting_started.html"
			echo "Please see https://github.com/TauferLab/Src_ANACIN-X for a full list of necessary installs."
			exit ;;
                * ) echo "Please respond with either yes or no: " ;;
        esac
done
read -p "Please provide a name for a project spack environment.  It can be anything. (Press enter for default anacin_spack_env) " user_spack_name
while true; do
	read -p "Do you already have the Conda package manager installed? (yes/no) " user_has_conda
	case ${user_has_conda} in
		[yY] | [yY][eE][sS] ) has_conda="yes"; break ;;
		[nN] | [nN][oO] ) echo "You will need to set up use of Anaconda prior to installation."
			echo "Please review instructions for how to do so at https://conda.io/projects/conda/en/latest/user-guide/install/index.html"
			echo "Please see https://github.com/TauferLab/Src_ANACIN-X for a full list of necessary installs."
			exit ;;
                #[nN] | [nN][oO] ) has_conda="no";  read -p "Where would you like to install Conda? (Press enter for your home directory.) " user_conda; break ;;
                * ) echo "Please respond with either yes or no: " ;;
	esac
done



### Define variables to pass to install script

# Options of yes or no
#has_spack="${user_has_spack:="yes"}"
#has_conda="${user_has_conda:="yes"}"
#has_c_comp="${user_has_comp:="yes"}"
#has_mpi="${user_has_mpi:="yes"}"
#has_ssh_key="${user_has_ssh:="yes"}"

# Options of openmpi, mvapich2, mpich
mpi_name="${user_mpi_name:="openmpi"}"

# Options of mac, linux86, linuxP9
os_for_conda="${user_os:="linux86"}"

# Needs to be correct path if on machine
#conda_path="${user_conda:=""}"
#spack_path="${user_spack:=""}"

# Can be anything
spack_env_name="${user_spack_name:="anacin_spack_env"}"


#echo ${mpi_name}
. anacin_deps.sh ${mpi_name} ${os_for_conda} ${spack_env_name} ${has_spack} ${has_conda} ${has_c_comp} ${has_mpi} ${has_ssh_key} 


