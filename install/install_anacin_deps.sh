#!/usr/bin/env bash


# Take Input Variables
user_mpi_name=$1
user_os=$2
user_spack_name=$3

has_spack=${4:-"yes"}
has_conda=${5:-"yes"}
has_c_comp=${6:-"yes"}
has_mpi=${7:-"yes"}
has_ssh=${8:-"yes"}


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


# Things to do:
#   Don't try to find external MPI.  If they have MPI already, don't try to load it here and tell user to update environment file
#   Don't find compilers here.  If user has specific c compiler, tell them to call spack compiler find prior to making environment and then update compilers.yaml file.

# Install zlib
echo
echo "Set up and Activate Spack Environment"
echo ${progress_delimiter}
#path_to_spack=$(which spack)
#spack_root=${path_to_spack%/bin/spack}
#. ${spack_root}/share/spack/setup-env.sh
spack install zlib
echo ${progress_delimiter}
# Create and activate spack environment
echo ${progress_delimiter}
spack env create ${spack_env} ./anacin_env.yaml
echo ${progress_delimiter}
#. /home/mushi11/spack/share/spack/setup-env.sh
spack env activate ${spack_env}
#echo "spack env activate ${spack_env}" >> ~/.bashrc
echo ${progress_delimiter}
echo "Done Activating Spack Environment"
echo

#if [ "yes" = "no" ]; then
# Spack compiler link
echo
echo "Link Spack to External Compiler and MPI"
echo ${progress_delimiter}
#echo "Link the external compiler to spack"
#c_comp=$(which icc)
#spack compiler find
echo ${progress_delimiter}
# Spack external mpi find?
echo ${progress_delimiter}
if [ ${has_mpi} = "yes" ]; then
    spack external find ${mpi_name}
fi
#echo ${mpi_name}
echo ${progress_delimiter}
echo "Done Linking Spack"
echo
#fi

# Spack concretize (we need to update the cmake identification and the spdlog ^cmake install)
echo
echo "Concretize and Install Spack Packages"
echo ${progress_delimiter}
spack concretize
echo ${progress_delimiter}
# Spack install
echo ${progress_delimiter}
spack install
despacktivate
spack install boost@1.70.0+atomic+chrono~clanglibcpp~context~coroutine cxxstd=98 +date_time~debug+exception~fiber+filesystem+graph~icu+iostreams+locale+log+math+mpi+multithreaded~numpy~pic+program_options~python+random+regex+serialization+shared+signals~singlethreaded+system~taggedlayout+test+thread+timer~versionedlayout visibility=hidden +wave ^${mpi_name}
spack env activate ${spack_env}
echo ${progress_delimiter}



# Load packages
echo
echo "Loading Spack Packages"
echo ${progress_delimiter}
echo
if [ ${has_mpi} == "no" ]; then
    spack load ${mpi_name};
fi
spack load libunwind;
spack load boost;
spack load cmake@3.22.6;
spack load nlohmann-json;
spack load spdlog;
spack load igraph;
spack load eigen;
echo ${progress_delimiter}
echo "Done Loading Spack Packages"
echo

# Add conda-forge to channels
echo ${progress_delimiter}
path_to_conda=$(which conda)
export PATH=${path_to_conda%/conda}:$PATH
conda config --append channels conda-forge
echo ${progress_delimiter}
echo "Done Setting up Conda"
echo


# conda install packages
echo
echo "Installing Conda Packages"
echo ${progress_delimiter}
conda install -y ruptures pyelftools pkg-config pkgconfig eigen=3.3.7
echo ${progress_delimiter}
echo "Done Installing Conda Packages"
echo

# Install most pip packages
echo
echo "Installing Pip Packages"
echo ${progress_delimiter}
pip install grakel==0.1.8
pip install python-igraph==0.9.11
pip install ipyfilechooser==0.6.0
conda install -y mpi4py
echo ${progress_delimiter}

# Set up to install graphkernels
echo ${progress_delimiter}

eigpath=$(pkg-config --variable=pcfiledir eigen3)
eigpath="${eigpath}/eigen3.pc"
sed -i 's/include\/eigen3/include/' ${eigpath}
pip install graphkernels==0.2.1
sed -i 's/include/include\/eigen3/' ${eigpath}
spack unload eigen@3.3.7
spack load eigen@3.3.7
echo ${progress_delimiter}
echo "Done Installing Pip Packages"
echo







