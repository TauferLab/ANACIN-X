#!/usr/bin/env bash


# Take Input Variables
user_mpi_name=$1
user_os=$2
user_conda=$3
user_spack=$4
user_mpi_name=$5

has_spack=${6:-"yes"}
has_conda=${7:-"yes"}
has_c_comp=${8:-"yes"}
has_mpi=${9:-"yes"}
has_ssh=${10:-"yes"}


# Define Conditionals for Installs
mpi_name="${user_mpi_name:="openmpi"}"
spack_env="${user_spack_name:="anacin_spack_env"}"
conda_path="${user_conda:=""}"
spack_path="${user_spack:=".."}"
os_for_conda="${user_os:="linux86"}"


### Create Delimiter and Workflow Variables
n_columns=$(stty size | awk '{print $2}')
progress_delimiter=""
for i in `seq 1 ${n_columns}`;
do
    progress_delimiter+="-"
done


# Things to Do
#   Request whether user needs/has spack, conda, c compiler, or mpi.
#   Request os version of conda
#   Have Spack environment be named by user with default of anacin_spack_env
#   Have user define conda and spack path
#   Ensure user has ssh key set up (Needs to be in readme, but could optionally include a conditional here)
#   Set MPI package name in external find
#   Automate cflag updates for graphkernels


### Set Up Spack Package Manager
# Clone Spack
echo
if [ ${has_spack} = no ]; then
    echo "Cloning and Activating Spack"
    echo ${progress_delimiter}
    cd ${spack_path}
    git clone https://github.com/spack/spack.git
    cd -
    echo ${progress_delimiter}
fi

# Add Spack to bashrc
echo ${progress_delimiter}
echo ". ${spack_path}/spack/share/spack/setup-env.sh" >> ~/.bashrc
. ${spack_path}/spack/share/spack/setup-env.sh
echo ${progress_delimiter}
echo "Done Preparing Spack"
echo

# Install zlib
echo
echo "Set up and Activate Spack Environment"
echo ${progress_delimiter}
spack install zlib
echo ${progress_delimiter}
# Create and activate spack environment
echo ${progress_delimiter}
spack env create ${spack_env} ./Src_ANACIN-X/anacin_env.yaml
spack env activate ${spack_env}
echo "spack env activate ${spack_env}" >> ~/.bashrc
echo ${progress_delimiter}
echo "Done Activating Spack Environment"
echo


# Spack compiler link
echo
echo "Link Spack to External Compiler and MPI"
echo ${progress_delimiter}
echo "Link the external compiler to spack"
spack compiler find
echo ${progress_delimiter}
# Spack external mpi find?
echo ${progress_delimiter}
spack external find -t ${mpi_name}
echo ${progress_delimiter}
echo "Done Linking Spack"
echo

# Spack concretize (we need to update the cmake identification and the spdlog ^cmake install)
echo
echo "Concretize and Install Spack Packages"
echo ${progress_delimiter}
spack concretize
echo ${progress_delimiter}
# Spack install
echo ${progress_delimiter}
spack install
echo ${progress_delimiter}

# Load packages
echo
echo "Loading Spack Packages"
echo ${progress_delimiter}
source ./load_spack.sh
echo ${progress_delimiter}
echo "Done Loading Spack Packages"
echo


### Set Up Conda Packages
# wget Anaconda
echo
echo "Setting up Conda"
if [ ${os_for_conda} = "linux86" ]; then
    echo ${progress_delimiter}
    wget https://repo.anaconda.com/archive/Anaconda3-2020.11-Linux-x86_64.sh
    echo ${progress_delimiter}
    # Install conda with bash script
    echo ${progress_delimiter}
    bash Anaconda3-2020.11-Linux-x86_64.sh -b? -p ${conda_path}
    echo ${progress_delimiter}
fi
if [ ${os_for_conda} = "linuxP9" ]; then
    echo ${progress_delimiter}
    wget https://repo.anaconda.com/archive/Anaconda3-2020.11-Linux-ppc64le.sh
    echo ${progress_delimiter}
    # Install conda with bash script
    echo ${progress_delimiter}
    bash Anaconda3-2020.11-Linux-ppc64le.sh -b? -p ${conda_path}
    echo ${progress_delimiter}
fi
if [ ${os_for_conda} = "mac" ]; then
    echo ${progress_delimiter}
    wget https://repo.anaconda.com/archive/Anaconda3-2020.11-MacOSX-x86_64.sh
    echo ${progress_delimiter}
    # Install conda with bash script
    echo ${progress_delimiter}
    bash Anaconda3-2020.11-MacOSX-x86_64.sh -b? -p ${conda_path}
    echo ${progress_delimiter}
fi

# Update bashrc to include conda in path
echo ${progress_delimiter}
echo "export PATH=./anaconda3/bin:$PATH" >> ~/.bashrc
echo ${progress_delimiter}
# Add conda-forge to channels
echo ${progress_delimiter}
conda config --append channels conda-forge
echo ${progress_delimiter}
echo "Done Setting up Conda"
echo

# conda install packages
echo
echo "Installing Conda Packages"
echo ${progress_delimiter}
conda install -y ruptures
conda install -y pyelftools
conda install -y pkg-config
conda install -y pkgconfig
conda install -y eigen=3.3.7
echo ${progress_delimiter}
echo "Done Installing Conda Packages"
echo

# Install most pip packages
echo
echo "Installing Pip Packages"
echo ${progress_delimiter}
pip install grakel==0.1b7
pip install python-igraph
pip install scikit-learn==0.22.1
echo ${progress_delimiter}

# Set up to install graphkernels
echo ${progress_delimiter}
spack unload eigen
# Edit eigen cflags for graphkernels install
# Undo edit to eigen cflags
spack load eigen
echo ${progress_delimiter}
echo "Done Installing Pip Packages"
echo







