# ANACIN-X
## Project Overview
Runtime non-determinism in High Performance Computing (HPC) applications presents steep challenges for computational reproducibility and correctness. These challenges are magnified in the context of complex scientific codes where the links between observable non-determinism and root causes are unclear. This repository contains a suite of tools for studying non-deterministic behavior in MPI applications. The core components of this tool suite include:
* `dumpi_to_graph` - A tool for building event graphs (i.e., graph-structured models of inter-process or inter-thread communication during an execution) from sets of trace files. 
* `CSMPI` - A PMPI module for tracing call-stacks of MPI function invocations. By tracing call-stacks in conjunction with a record of communication behavior, runtime non-determinism can be linked to its potential root-causes in source code. 
* `event_graph_analysis` - A collection of Python scripts for analyzing and visualizing event graphs both in isolation and in batches to recognize patterns in non-deterministic communication. 

## Installation
Assuming all dependenices are installed, you should be able to build all of ANACIN-X's components by running the `setup.sh` script.

Where possible, we recommend installing ANACIN-X's dependencies with Spack and Conda.

### Spack:
Spack is a package manager with good support for scientific/HPC software. To use Spack you will need Python. We recommend you install Spack *and* enable Spack's shell integration. 

To install Spack, follow the instructions at: https://spack.readthedocs.io/en/latest/getting_started.html

In particular, make sure to follow the instructions under "Add Spack to the Shell". This step will allow software installed with Spack to be loaded and unloaded as [environment modules.](https://spack.readthedocs.io/en/latest/getting_started.html#installenvironmentmodules) 

### Conda:
Conda is a cross-language package, dependency, and environment manager. We use Conda to manage the dependencies of ANACIN-X's Python code. 

To install Conda, follow the instructions at: https://conda.io/projects/conda/en/latest/user-guide/install/index.html


## Dependencies:
### Event Graph Construction:
Our tool for building event graphs from trace files, `dumpi_to_graph`, has the following dependencies:
* MPI
* Boost
* CMake
* igraph

### Call-Stack Tracing
Our call-stack-tracing PMPI module, `CSMPI`, has the following dependencies:
* MPI
* Boost
* Cmake
* Libunwind

### Event Graph Analysis 
We use the following Python modules:
* numpy
* igraph-python
* matplotlib
* graphkernels
* ruptures
* pyelftoolsS
The graphkernels module depends on:
* pkg-config
* Eigen

