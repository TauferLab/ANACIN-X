# ANACIN-X
## Project Overview
Runtime non-determinism in High Performance Computing (HPC) applications presents steep challenges for computational reproducibility and correctness. These challenges are magnified in the context of complex scientific codes where the links between observable non-determinism and root causes are unclear. This repository contains a suite of tools for studying non-deterministic behavior in MPI applications. The core components of this tool suite include:
* `dumpi_to_graph` - A tool for building event graphs (i.e., graph-structured models of inter-process or inter-thread communication during an execution) from sets of trace files. 
* `CSMPI` - A PMPI module for tracing call-stacks of MPI function invocations. By tracing call-stacks in conjunction with a record of communication behavior, runtime non-determinism can be linked to its potential root-causes in source code. 
* `event_graph_analysis` - A collection of Python scripts for analyzing and visualizing event graphs both in isolation and in batches to recognize patterns in non-deterministic communication. 

## Installation
We recommend installing ANACIN-X's dependencies with Spack. 

### Installation: Spack
Spack is a package manager with good support for scientific/HPC software. To use Spack you will need Python. We recommend you install Spack *and* enable Spack's shell integration. 

To install Spack:
* git clone https://github.com/spack/spack.git
* Throughout the rest of installation, we will refer to the location that Spack is cloned to as `$SPACK_ROOT`

To enable Spack's shell integration (For bash/zsh users):
* Add `$SPACK_ROOT/bin` to your `PATH`
* Run `. $SPACK_ROOT/share/spack/setup-env.sh`
* Run `spack bootstrap` 
The last step will install environment-modules and allow software installed with Spack to be loaded and unloaded as environment modules. 

### Installation: dumpi\_to\_graph dependencies
Our tool for building event graphs from trace files, `dumpi_to_graph`, has the following dependencies:
* MPI
* Boost
* CMake
* igraph

### Installation: CSMPI dependencies
Our call-stack-tracing PMPI module, `CSMPI`, has the following dependencies:
* MPI
* Boost
* Cmake
* Libunwind

### Installation: event_graph_analysis dependencies
We use the following Python modules:
* numpy
* igraph-python
* matplotlib
* graphkernels
* ruptures
* pyelftools

We recommend installing these dependencies with Spack (with the possible exception of MPI). If you have set up Spack as described above, you may simply run the following scripts:
* `install/install_dumpi_to_graph_dependencies.sh`
* `install/install_csmpi_dependencies.sh`
* `install/install_ega_dependencies.sh`

