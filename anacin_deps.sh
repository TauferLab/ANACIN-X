#!/usr/bin/env bash


### Create Delimiter and Workflow Variables
n_columns=$(stty size | awk '{print $2}')
progress_delimiter=""
for i in `seq 1 ${n_columns}`;
do
    progress_delimiter+="-"
done
spack_env="anacin_spack_env"

# Things to Do
#   Request whether user needs/has spack, conda, c compiler, or mpi
#   Do we need to select OS specific versions of Conda
#   Have Spack environment be named by user with default of anacin_spack_env
#   Ensure user has ssh key set up (Needs to be in readme, but could optionally include a conditional here)
#   Set MPI package name in external find
#   Automate cflag updates for graphkernels
#   Set up spack package loading (Could benefit from separate script to be able to reload packages.  That script could also be optionally called from bashrc)
#   Add Anacin-x root path as an environment variable through bashrc to have well defined access to files in the project?


### Set Up Spack Package Manager
# Clone Spack
echo
echo ${progress_delimiter}
echo "Cloning and Activate Spack"
git clone https://github.com/spack/spack.git
echo ${progress_delimiter}

# Add Spack to bashrc
echo ${progress_delimiter}
echo ". ./spack/share/spack/setup-env.sh" >> ~/.bashrc
. ./spack/share/spack/setup-env.sh
echo ${progress_delimiter}
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
spack external find -t  
echo ${progress_delimiter}
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

echo ${progress_delimiter}
echo


### Set Up Conda Packages
# wget Anaconda
echo
echo "Setting up Conda"
echo ${progress_delimiter}
wget https://repo.anaconda.com/archive/Anaconda3-2020.11-Linux-x86_64.sh
echo ${progress_delimiter}
# Install conda with bash script
echo ${progress_delimiter}
bash Anaconda3-2020.11-Linux-x86_64.sh
echo ${progress_delimiter}
# Update bashrc to include conda in path
echo ${progress_delimiter}
echo "export PATH=./anaconda3/bin:$PATH" >> ~/.bashrc
echo ${progress_delimiter}
# Add conda-forge to channels
echo ${progress_delimiter}
conda config --append channels conda-forge
echo ${progress_delimiter}

# conda install packages
echo
echo "Installing Conda Packages"
echo ${progress_delimiter}
conda install ruptures
conda install pyelftools
conda install pkg-config
conda install pkgconfig
conda install eigen=3.3.7
echo ${progress_delimiter}
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
echo ${progress_delimiter}
echo







