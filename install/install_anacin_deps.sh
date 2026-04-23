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
python_bin="${ANACIN_X_PYTHON:-}"
script_dir="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd)"
spack_manifest="${script_dir}/anacin_env.yaml"
if [ -n "${CONDA_PREFIX:-}" ] && [ -d "${CONDA_PREFIX}/bin" ]; then
    export PATH="${CONDA_PREFIX}/bin:${PATH}"
fi
if [ -z "${python_bin}" ] && [ -n "${CONDA_PREFIX:-}" ] && [ -x "${CONDA_PREFIX}/bin/python" ]; then
    python_bin="${CONDA_PREFIX}/bin/python"
fi
if [ -z "${python_bin}" ] && [ -n "${CONDA_PREFIX:-}" ] && [ -x "${CONDA_PREFIX}/bin/python3" ]; then
    python_bin="${CONDA_PREFIX}/bin/python3"
fi
if [ -z "${python_bin}" ]; then
    python_bin="$(command -v python || command -v python3)"
fi

### Create Delimiter and Workflow Variables
n_columns=$(stty size 2>/dev/null | awk '{print $2}')
n_columns=${n_columns:-80}
progress_delimiter=""
for i in `seq 1 ${n_columns}`;
do
    progress_delimiter+="-"
done


# Things to do:
#   Don't try to find external MPI.  If they have MPI already, don't try to load it here and tell user to update environment file
#   Don't find compilers here.  If user has specific c compiler, tell them to call spack compiler find prior to making environment and then update compilers.yaml file.

if ! command -v spack >/dev/null 2>&1; then
    echo "Error: spack was not found in PATH. Source Spack before running this script."
    echo "Example: . /path/to/spack/share/spack/setup-env.sh"
    return 1 2>/dev/null || exit 1
fi

if ! command -v conda >/dev/null 2>&1; then
    echo "Error: conda was not found in PATH. Activate Conda before running this script."
    return 1 2>/dev/null || exit 1
fi

if [ -z "${CONDA_PREFIX:-}" ]; then
    echo "Error: no active Conda environment detected."
    echo "Please run: conda activate <your-conda-environment>"
    return 1 2>/dev/null || exit 1
fi

python_version="$("${python_bin}" -c 'import sys; print(f"{sys.version_info.major}.{sys.version_info.minor}")')"
if [ "${python_version}" != "3.8" ]; then
    echo "Error: ANACIN-X Python dependencies require a Python 3.8 Conda environment."
    echo "Detected Python ${python_version} at ${python_bin}."
    echo "Please run: conda create -n anacin-x python=3.8 -y && conda activate anacin-x"
    return 1 2>/dev/null || exit 1
fi

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
if spack env list | awk '{print $1}' | grep -Fxq "${spack_env}"; then
    spack_env_dir="$(spack location -e "${spack_env}")"
    echo "Refreshing existing Spack environment manifest: ${spack_env_dir}/spack.yaml"
    cp "${spack_manifest}" "${spack_env_dir}/spack.yaml"
else
    spack env create ${spack_env} "${spack_manifest}"
fi
echo ${progress_delimiter}
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
spack concretize -f --deprecated
echo ${progress_delimiter}
# Spack install
echo ${progress_delimiter}
spack install --deprecated
echo ${progress_delimiter}



# Load packages
echo
echo "Loading Spack Packages"
echo ${progress_delimiter}
echo
if [ ${has_mpi} == "yes" ]; then
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
path_to_conda=$(command -v conda)
export PATH=${path_to_conda%/conda}:$PATH
conda config --prepend channels conda-forge
echo ${progress_delimiter}
echo "Done Setting up Conda"
echo


# conda install packages
echo
echo "Installing Conda Packages"
echo ${progress_delimiter}
conda install -y -c conda-forge ruptures pyelftools pkg-config pkgconfig mpi4py libstdcxx-ng libgcc-ng numpy pip
echo ${progress_delimiter}
echo "Done Installing Conda Packages"
echo

# Install most pip packages
echo
echo "Installing Pip Packages"
echo ${progress_delimiter}
${python_bin} -m pip install grakel==0.1.8 || return 1 2>/dev/null || exit 1
${python_bin} -m pip install python-igraph==0.9.11 || return 1 2>/dev/null || exit 1
${python_bin} -m pip install ipyfilechooser==0.6.0 || return 1 2>/dev/null || exit 1
${python_bin} -m pip install psutil || return 1 2>/dev/null || exit 1
echo ${progress_delimiter}

# Set up to install graphkernels
echo ${progress_delimiter}

eigpath=$(pkg-config --variable=pcfiledir eigen3)
eigpath="${eigpath}/eigen3.pc"
sed -i 's/include\/eigen3/include/' ${eigpath}
${python_bin} -m pip install graphkernels==0.2.1 || return 1 2>/dev/null || exit 1
sed -i 's/include/include\/eigen3/' ${eigpath}
spack unload eigen@3.3.7
spack load eigen@3.3.7
echo ${progress_delimiter}
echo "Done Installing Pip Packages"
echo
