<p align="center">
    <img src="anacin-logo.png" width="350">
</p>

# ANACIN-X
## Software Overview
Runtime non-determinism in High Performance Computing (HPC) applications presents steep challenges for computational reproducibility and correctness. These challenges are magnified in the context of complex scientific codes where the links between observable non-determinism and root causes are unclear. This repository contains a suite of tools for trace-based analysis of non-deterministic behavior in MPI applications. The core components of this tool suite are: 
* A Workflow for Characterizing Root Sources of Non-Determinism as Graph Similarity: To meet the challenges of runtime non-determinism in HPC applications, we design a workflow for approximating the measure of non-determinism in a programs execution via graph kernel analysis.  This workflow is broken down into parts below this list.
* Use Case Communication Patterns: We implement some respresentative sample MPI point-to-point, non-deterministic communication patterns for illustrating the value of the ANACIN-X workflow in the process of debugging non-determinism.  We provide the user with the option to choose one of three communication patterns for a given executation of ANACIN-X: a message race, the Algebraic Multigrid 2013 (AMG 2013) pattern, or the Unstructured Mesh pattern.
  * In each case, we quantify and vary the amount of non-determinism ranging from 0% non-determinism up to 100% non-determinism.
  * For more information about the communication patterns in question, please see the most recent publication in the publications section of this README.md document.
* Kernel Distance Visualization: To help the user view the relationship between kernel distance and percent of non-determinism in a given communication pattern, we provide 2 ways to create a .png figure for data from a given set of runs: Use a Jupyter notebook to generate and view the figure or use a command line tool to generate the figure.
  * Instructions for using these visualization options are provided in the 'Result Visualization' section below.
  
The workflow for characterizing root sources of non-determinism as graph similarity is broken up into 3 stages.  We describe each in more detail:
  * Execution Tracing: We use a stack of PMPI modules composed with [PnMPI](https://github.com/LLNL/PnMPI) to trace executions of non-deterministic MPI applications.  In particular, we use the [sst-dumpi](https://github.com/TauferLab/sst-dumpi/tree/b47bb77ccbe3b87d585e3701e1a5c2f8d3626176) and the [Pluto](https://github.com/TauferLab/Src_Pluto/tree/main) tracing modules.
    * sst-dumpi traces relationships between MPI events.  With this, we can determine the message order of these MPI events in time.
    * Pluto traces memory addresses of MPI requests associated with non-blocking MPI events.  We use these memory addresses as unique identifiers of MPI requests to distinguish between different types of non-blocking MPI events
  * Event Graph Construction: We convert each execution's traces into a graph-structured model of the interprocess communication that took place during the execution using the [dumpi_to_graph](https://github.com/TauferLab/Src_dumpi_to_graph/tree/3966d25a916ddf0cd5e4e71ce71702798c0f39e1) tool.
    * dumpi_to_graph takes information about the addresses of MPI events from Pluto and about happens before MPI relationships from sst-dumpi to construct a unique directed acyclic graph of the [graphml](https://en.wikipedia.org/wiki/GraphML) format which models the underlying communication pattern.
  * Event Graph Kernel Analysis: We implement workflows for identifying root causes of non-deterministic behavior using the Weisfeiller-Lehmann Subtree (WLST) graph kernel.  This kernel analysis is implemented using the [GraKeL](https://github.com/ysig/GraKeL) and the [GraphKernels](https://github.com/BorgwardtLab/GraphKernels) software packages.
    * The WLST graph kernel iteratively encodes graph structure into node labels by refining each node label based on its neighbors labels.  More information on WLST kernels can be found at **.
    * The GraKeL and GraphKernels are both software packages that implement a variety of kernels on graph structured data.  

## Installation

If you're running your version of the project on an instance of the [Jetstream cloud computer](https://jetstream-cloud.org), use the image "Ubuntu20.04_Anacin-X" and skip ahead to the subsection below about installing ANACIN-X.  Otherwise, continue reading here to ensure all dependencies are installed.

If you haven't already, you'll need to install the Spack and Conda package managers.

### Spack:
Spack is a package manager with good support for scientific/HPC software. To use Spack you will need Python. We recommend you install Spack *and* enable Spack's shell integration. 

To install Spack, follow the instructions at: [Spack Install](https://spack.readthedocs.io/en/latest/getting_started.html)

In particular, make sure to follow the instructions under "Shell support". This step will allow software installed with Spack to be loaded and unloaded as [environment modules.](https://spack.readthedocs.io/en/latest/getting_started.html#installenvironmentmodules) 

### Conda:
Conda is a cross-language package, dependency, and environment manager. We use Conda to manage the dependencies of ANACIN-X's Python code.  We strongly recommend using the Anaconda installation of the package manager rather than the Miniconda version so that you can have Jupyter installed on your machine for data visualization.

To install Conda, follow the instructions at: [Conda Install](https://conda.io/projects/conda/en/latest/user-guide/install/index.html)

Before continuing, make sure to activate your version of conda:

```
source ~/.bashrc
```

### ANACIN-X:
You will need to first download the project through git using

```
git clone https://github.com/TauferLab/ANACIN-X.git
```

Note that Spack and Conda will need to be installed and set up beforehand as described above, unless you're on Jetstream.  If there is a specific C compiler that you wish to have used on your machine, please see the 'Special Case' section below.

Now that your environment is prepared and the project is on your local machine, be sure to enter the project root for setup with the command:

```
cd ANACIN-X
```

If you're using the Jetstream cloud computer image for Anacin-X titled "Ubuntu20.04_Anacin-X", you can skip this next command.  Otherwise, we strongly recommend installing the dependencies for the project with:

```
. setup_deps.sh
``` 

The script will begin by verifying some information.  Follow the prompts at the beginning, and then the installation will run on its own.  The installation of all dependencies may take some time to complete.

Assuming all dependenices are installed and loaded, you should then be able to build all of ANACIN-X's components by running

```
. setup.sh
```

### Special Case:

If you have a specific external C compiler installed that you wish to use, you will need to edit the compilers.yaml file in spack:
* First open the compilers.yaml file to determine which compilers are added to the system.  This can be done with the command:

```
spack config edit compilers
```

* If you don't see information for your compiler in the listed options, exit the file and make sure your compiler is installed and loaded.  Then use the following command before reopening the compilers.yaml file.

```
spack compiler find
```

* Within the compilers.yaml file, delete information for all compilers other than the one you wish to use.
* Save and quit the file, then try to install the ANACIN-X dependencies.


## Dependencies:
### Installed by User
The following packages need to be installed by the user:
* spack
* conda
* C Compiler (ex. GCC)

### Installed by Spack
The following packages will be installed via spack:
* boost
* cmake
* igraph
* nlohmann-json
* libunwind
* spdlog

### Installed by Conda
The following packages will be installed via conda:
* ruptures
* pyelftools
* pkg-config
* pkgconfig
* eigen (first gets installed through Spack)

### Installed by Pip
The following packages will be installed via pip:
* grakel
* python-igraph
* mpi4py
* graphkernels
* ipyfilechooser

### Submodule Packages
The following packages will be installed as submodules to the installation of ANACIN-X:
* [PnMPI](https://github.com/LLNL/PnMPI/tree/f6fcc801ab9305352c510420c6439b7d48a248dc)
* [sst-dumpi](https://github.com/TauferLab/sst-dumpi/tree/b47bb77ccbe3b87d585e3701e1a5c2f8d3626176)
* [Pluto](https://github.com/TauferLab/Src_Pluto/tree/main)
* [dumpi_to_graph](https://github.com/TauferLab/Src_dumpi_to_graph/tree/3966d25a916ddf0cd5e4e71ce71702798c0f39e1)


## Running ANACIN-X:

Use the 'comm_pattern_analysis.sh' script to generate traces of a selected communication pattern and perform analysis on the event graphs.  Make sure that the system you're running on supports the inputs you provide from the options below.:

The following command line switches can be used to define parameters for your job submission:
* -p        : Defines the size of the mpi communicator 
                used when generating communication patterns. 
                (Default 4 MPI processes)
* -i         : Defines the number of times a given communication 
                pattern appears in a single execution of ANACIN-X. 
                If running the message race communication patter,
                it's recommended to set this to at least 10.
                (Default 1 iteration)
* -s        : The size in bytes of the messages passed when generating 
                communication patterns. 
                (Default 512 bytes)
* -n        : The number of compute nodes requested for running 
                the ANACIN-X workflow. 
                If you're running on an unscheduled system,
                this value should be set to 1.
                (Default 1 node)
* -r         : The number of runs to make of the ANACIN-X workflow. 
                (Default 2 executions)
* -o        : If used, allows the user to define their own path to 
                store output from the project. 
                Be sure to define an absolute path that can exist on your machine.
                Use a different path when running multiple times on the same settings to avoid overwriting.
                (Defaults to the directory '$HOME/comm_pattern_output')
* -c        : When running the unstructured mesh communication pattern, 
                use this with 3 arguments to define the grid coordinates. 
                (Ex. -c 2 3 4)
* -v        : If used, will display the execution settings prior 
                to running the execution.
* -h        : Used to display the list of switch options.

If you're running on a system that uses the Slurm scheduler, then the following switches can be used to define settings for job submission:
* -sq       : Defines the queue to submit Slurm jobs to. 
                (Defaults to the "normal" queue)
* -st        : A maximum time limit in minutes on the time provided to jobs submitted. 
                (Default 10 minutes)

If you're running on a system that uses the LSF scheduler, then the following switch can be used to define settings for job submission:
* -lq        : Defines the queue to submit LSF jobs to. 
                (Defaults to the "normal" queue)
* -lt        : A maximum time limit in minutes on the time provided to jobs submitted.
                (Default 10 minutes)
                

If the project is run with settings that are too small, then the communication pattern generation may end up not being non-deterministic.  A few things can be done to increase the odds of inducing non-determinism in a simulation:
* It is good to run on a large number of processes (at least 10) and a large number of runs (at least 50) to increase the odds of non-determinism arising.
* By running a communication pattern with multiple iterations (using the -i flag), the user can cause more non-determinism.  This is particularly important when running the message race communication pattern.
* Running with a small message size (using the -s flag) can increase the likelihood of non-determinism.
* Running the program across multiple compute nodes (using the -n flag) can help to cause more non-determinism.

Below is an example run of the script as one might submit it to run message_race on an unscheduled system.

```
. ./comm_pattern_analysis.sh -p 20 -i 10 -v -r 100 -o $HOME/message_race_sim_1
```

Below is another example run of the script as one might submit it on the Stampede2 cluster computer:

```
. ./comm_pattern_analysis.sh -p 48 -n 2 -v -r 50 -sq "skx-normal" -o $WORK2/anacinx_output_1
```

Once the script has started running, follow the prompts at the beginning.  You will need to input a communication pattern to generate.  You can choose between any of the communication patterns listed in the supported settings section below with these corresponding formats: message_race, amg2013, unstructured_mesh.

The script will also request which scheduler your computing system employs.  Please input one of the following: lsf, slurm, unscheduled.

Be aware that if you run the project on some machines and some job queues, there will be a limit to the number of jobs that can be submitted.  In such cases, you may lose some jobs if you try to run the program with settings that produce more jobs than are allowed in the queue being used.

### Result Visualization: 

There are a few methods to do visualization of the kernel distance data from ANACIN-X.  We strongly recommend using Jupyter Notebooks if you can pull it up from your machine.  The following methods will work to visualize the data.

#### Method 1 - Jupyter

If you can use Jupyter to visualize the data for the project, open Jupyter from your machine.  Within Jupyter, find the file titled **visualization.ipynb** in the same directory as the script you used to produce your data (that is the root of your project).

By opening this visualization script and following the instructions within, you can visualize the kernel distance data.

#### Method 2 - Command Line Visualization

If you can't use Jupyter to visualize the data, then we recommend using the command line python tool to generate the png images.  This will take a few key steps:

You will first need to identify the inputs to the visualization script.  These can be found in 2 ways.
1. The first way to find the inputs is to look at the last 3 lines printed to standard out from your run.  There you can find:
  * The path to your kernel distance (KDTS) data file. If you ran the unstructured mesh communication pattern, a separate KDTS file will be found in each 'nd_neighbor_fraction' directory.
  * The communication pattern used.
  * The path to your kernel config JSON file.
2. The second way to find the inputs is to navigate to your output directory in the following way.
  * Navigate to the directory that your output was stored in from your run and save the full path including the file name of the json file stored there.
  * Open the run_config.txt file stored in that directory and save the name of the communication pattern as listed in the first line item.  Then exit that file.
  * Follow the output directory structure down based on the inputs you gave to set the project with until you find a file titled 'kdts.pkl' and save the full path to your 'kdts.pkl' file so that it can be used when calling the visualization script.

Once you've gathered the needed inputs, return to the project directory where you submitted jobs from.  From there, input the following command:

```
python3 anacin-x/event_graph_analysis/visualization/make_message_nd_plot.py [Path to 'kdts.pkl' file with file name] [The type of communication pattern you used] [Path to kernel json used to generate kdts file] [The name of a file to store the visualization in (excluding the file type)] [--nd_neighbor_fraction <value> (only used for unstructured mesh communication pattern)]
```

A png file will be produced and placed in the working directory.  If you're doing your work and producing visualizations on a remote machine, remember to copy your png image to your local machine using a tool like scp to view the image.

### Supported Systems and Settings:

Currently, the software supports the following types of scheduler systems for job submission.  Make sure that you are running on one of these:
* LSF scheduled systems (ex. Tellico)
* Slurm scheduled systems (ex. Stampede2)
* Unscheduled systems (ex. Jetstream, personal computers)

When determining the number of times to run a given execution, be sure that it is set to more than 1.  Otherwise, kernel analysis will not work properly.

If you're implementing the Unstructured Mesh communication pattern, then set the 3 Unstructured Mesh coordinates such that their product is equal to the number of processes used.


## Project Team:

Developers:
* Nick Bell
* Dylan Chapp
* Kae Suarez
* Nigel Tan

Project Advisors:
* Dr. Sanjukta Bhowmick
* Dr. Michela Taufer (Project Lead)

## Publications:

D. Chapp, D. Rorabaugh, K. Sato, D. Ahn, and M. Taufer. **A Three-phase Workflow for General and Expressive Representations of Nondeterminism in HPC Applications.** *International Journal of High-Performance Computing Applications(IJHPCA), 1175-1184* (2019).

D. Chapp, K. Sato, D. Ahn, and M. Taufer. **Record-and-Replay Techniques for HPC Systems: A survey.** *Journal of Supercomputing Frontiers and Innovations, 5(1):11-30.* (2018).

D. Chapp, T. Johnston, and M. Taufer. **On the Need for Reproducible Numerical Accuracy through Intelligent Runtime Selection of Reduction Algorithms at the Extreme Scale.** *In Proceedings of IEEE Cluster Conference, pp. 166 – 175. Chicago, Illinois, USA.* September 8 – 11, 2015.

## Copyright and License:

BSD 3-Clause License

Copyright (c) 2019, Global Computing Lab
All rights reserved.

Redistribution and use in source and binary forms, with or without
modification, are permitted provided that the following conditions are met:

1. Redistributions of source code must retain the above copyright notice, this
   list of conditions and the following disclaimer.

2. Redistributions in binary form must reproduce the above copyright notice,
   this list of conditions and the following disclaimer in the documentation
   and/or other materials provided with the distribution.

3. Neither the name of the copyright holder nor the names of its
   contributors may be used to endorse or promote products derived from
   this software without specific prior written permission.

THIS SOFTWARE IS PROVIDED BY THE COPYRIGHT HOLDERS AND CONTRIBUTORS "AS IS"
AND ANY EXPRESS OR IMPLIED WARRANTIES, INCLUDING, BUT NOT LIMITED TO, THE
IMPLIED WARRANTIES OF MERCHANTABILITY AND FITNESS FOR A PARTICULAR PURPOSE ARE
DISCLAIMED. IN NO EVENT SHALL THE COPYRIGHT HOLDER OR CONTRIBUTORS BE LIABLE
FOR ANY DIRECT, INDIRECT, INCIDENTAL, SPECIAL, EXEMPLARY, OR CONSEQUENTIAL
DAMAGES (INCLUDING, BUT NOT LIMITED TO, PROCUREMENT OF SUBSTITUTE GOODS OR
SERVICES; LOSS OF USE, DATA, OR PROFITS; OR BUSINESS INTERRUPTION) HOWEVER
CAUSED AND ON ANY THEORY OF LIABILITY, WHETHER IN CONTRACT, STRICT LIABILITY,
OR TORT (INCLUDING NEGLIGENCE OR OTHERWISE) ARISING IN ANY WAY OUT OF THE USE
OF THIS SOFTWARE, EVEN IF ADVISED OF THE POSSIBILITY OF SUCH DAMAGE.




