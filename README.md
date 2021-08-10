<p align="center">
    <img src="anacin_pngs/anacin-logo.png" width="350">
</p>

# ANACIN-X

[![DOI](https://zenodo.org/badge/364344863.svg)](https://zenodo.org/badge/latestdoi/364344863)
[![Open in Code Ocean](https://codeocean.com/codeocean-assets/badge/open-in-code-ocean.svg)](https://doi.org/10.24433/CO.2809639.v1)

## Introduction

Non-deterministic results often arise unexpectedly in High Performance Computing (HPC) applications.  These make reproducible and correct results difficult to create.  As such, there is a need to improve the ability of software developers and scientists to comprehend non-determinism in their applications.  To this end, we present ANACIN-X.  This document is organized in the following order:

* The first section describes the components of the software.  
* The second section describes instructions for installation of the software.  **Please read this section carefully as there are a variety of different steps involved.**
* The third section lists the dependencies that the installation procedure will install on its own.  **We do not recommend installing all of the dependencies on your own.  Instead, use instructions in the installation section to install the dependencies, starting with those on installing Spack and Conda.**
* The fourth section describes how to run the software.  This is broken up into 3 main parts:
  1. How to run the software that produces kernel distance data.
  2. How to visualize data produced in the first part.
  3. Systems and settings that the project supports.
* At the end, we describe the following 3 things:
  1. The project team
  2. Publications associated with the software
  3. Copyright and license information
  
## Software Overview

This repository contains a suite of tools for trace-based analysis of non-deterministic behavior in MPI applications. The core components of this tool suite are as follows.  More detail for each can be found in sections below: 
* **A Framework for Characterizing Root Sources of Non-Determinism as Graph Similarity**: To meet the challenges of non-determinism in HPC applications, we design a workflow for approximating the measure of non-determinism in a programs execution via graph kernel analysis.  This workflow is broken down into the following three stages that are described in more detail below this list:
  1. Execution Trace Collection
  2. Event Graph Construction
  3. Event Graph Kernel Analysis
* **Use Case Communication Patterns for Testing**: So that the user can test the framework mentioned above, we implement some representative sample MPI point-to-point, non-deterministic communication patterns for illustrating the value of the ANACIN-X workflow in the process of debugging non-determinism.  We provide the user with the option to choose one of three communication patterns for a given executation of ANACIN-X: 
  1. Message Race
  2. The Algebraic Multigrid 2013 (AMG 2013) pattern
  3. The Unstructured Mesh pattern
* **Kernel Distance Visualization**: After executing the framework mentioned above on one of the provided use cases, the user will have access to kernel distance data related to the execution made.  To help the user view the relationship between kernel distance and percent of non-determinism in a given communication pattern, we provide 2 ways to create a .png figure for data from a given set of runs. 
  1. Use a Jupyter notebook to generate and view the figure
  2. Use a command line tool to generate the figure.
  
### Outline of the Framework for Characterizing Root Sources of Non-Determinism
The framework for characterizing root sources of non-determinism as graph similarity is broken up into 3 stages.  We describe each in more detail:
* **Execution Trace Collection**: We use a stack of PMPI modules composed with [PnMPI](https://github.com/LLNL/PnMPI) to trace executions of non-deterministic MPI applications.  In particular, we use the [sst-dumpi](https://github.com/TauferLab/sst-dumpi/tree/b47bb77ccbe3b87d585e3701e1a5c2f8d3626176) and the [Pluto](https://github.com/TauferLab/Src_Pluto/tree/main) tracing modules.
  * sst-dumpi traces relationships between MPI events.  With this, we can determine the message order of these MPI events in time.
  * Pluto traces memory addresses of MPI requests associated with non-blocking MPI events.  We use these memory addresses as unique identifiers of MPI requests to distinguish between different types of non-blocking MPI events
* **Event Graph Construction**: We convert each execution's traces into a graph-structured model of the interprocess communication that took place during the execution using the [dumpi_to_graph](https://github.com/TauferLab/Src_dumpi_to_graph/tree/3966d25a916ddf0cd5e4e71ce71702798c0f39e1) tool.
  * dumpi_to_graph takes information about the addresses of MPI events from Pluto and about happens before MPI relationships from sst-dumpi to construct a unique directed acyclic graph of the [graphml](https://en.wikipedia.org/wiki/GraphML) format which models the underlying communication pattern.
* **Event Graph Kernel Analysis**: We implement workflows for identifying root causes of non-deterministic behavior using the Weisfeiler-Lehmann Subtree (WLST) graph kernel.  This kernel analysis is implemented using the [GraphKernels](https://github.com/BorgwardtLab/GraphKernels) software package.
  * The WLST graph kernel iteratively encodes graph structure into node labels by refining each node label based on its neighbors labels.  More information on WLST kernels can be found in the paper ["Weisfeiller-lehmann graph kernels"](https://www.jmlr.org/papers/volume12/shervashidze11a/shervashidze11a.pdf) by Shervashidze et al.
  * GraphKernels is a software package that implements a variety of kernels on graph structured data.  
    
### Use Case Descriptions
We provide 3 benchmark use case communication patterns for the purpose of testing the ability of the ANACIN-X workflow to characterize non-determinism.  In each case, we quantify and vary the percentage of non-determinism present ranging from 0% non-determinism up to 100% non-determinism at intervals of 10%.  We provide a brief description below about each communication pattern.  For more information about the communication patterns in question, please see the most recent publication in the publications section of this README.md document.  The patterns are as follows:
* **Message Race**: 
  * When executed on N processes, this pattern consists of N-1 sender processes sending a single message to a root process that receives them in arbitrary order.  
  * It is the core pattern that models receiver-side non-determinism.
* **Algebraic Multigrid 2013 (AMG 2013)**: 
  * The AMG2013 communication pattern is extracted from the proxy application of the same name in the [CORAL Benchmark Suite](https://gitlab.com/arm-hpc/benchmarks/coral-2).
  * We select this pattern due to its expression of both receiver-side and sender-side non-determinism, a property that has been highlighted in prior work on communication non-determinism.
* **Unstructured Mesh**: 
  * This communication pattern is extracted from the [Chatterbug Communication Pattern Suite](https://github.com/hpcgroup/chatterbug).
  * It exhibits non-determinism due to a randomized process topology, resulting in run-to-run variation in terms of which processes communicate with which others.
  
### Kernel Distance Visualization
Here we provide a brief description of each tool for visualizing ANACIN-X kernel distance data.  Instructions for using these visualization options are provided in the 'Result Visualization' section farther down in this README.
* **Jupyter Notebook**:
  * As one method for visualizing kernel distance data, we created a Jupyter notebook which is able to display your .png visualization without needing to copy the .png file across machines.
  * For more information about Jupyter notebooks, see their website [here](https://jupyter.org).
* **Command Line Python Tool**:
  * You may not have easy access to Jupyter notebooks on the machine you run ANACIN-X from.  In that case, we provide instructions for generating the same visualization from the command line.
  * Those instructions can be found farther down this document in the section titled 'Result Visualization'.
  
If effective inputs are set when running the ANACIN-X software, the user will be able to use the .png visualization generated by one of the methods listed above to see how varying non-determinism in a communication pattern can correlate well with the kernel distance between different runs of that communication pattern.


## **Installation**

**Important**: Please read the instructions in this README in order.  Effective use of this software is dependent on correct installation of all dependencies.  Since there are a collection of dependencies, we provide tools for automating the process.  So read through the instructions carefully.

If you're running your version of the project on an instance of the [Jetstream cloud computer](https://jetstream-cloud.org), use the image ["Ubuntu20.04_Anacin-X"](https://use.jetstream-cloud.org/application/images/1056) and skip ahead to the subsection below about installing ANACIN-X.  If you're using a different Jetstream image or if you're not using Jetstream, continue reading here to ensure all dependencies get installed.

**If you haven't already, you will need to install the Spack and Conda package managers**, be sure to do so using the following instructions.  We will use these to help automate the installation of dependencies.

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

Note that Spack and Conda will need to be installed and set up beforehand as described above, unless you're using the Jetstream image listed above.  If there is a specific C compiler that you wish to have used on your machine, please see the 'Special Case' section below.

Now that your environment is prepared and the project is on your local machine, be sure to enter the project root for setup with the command:

```
cd ANACIN-X
```

If you're using the  [Jetstream cloud computer](https://jetstream-cloud.org) image for Anacin-X titled ["Ubuntu20.04_Anacin-X"](https://use.jetstream-cloud.org/application/images/1056), you can skip this next command.  Otherwise, we strongly recommend installing the dependencies for the project with:

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

Below is a list of dependencies for ANACIN-X.  **Note** that if you follow the procedures above for installation, you do not need to install the dependencies one at a time.  We strongly recommend using the scripts provided to install the software, as described in the "Installation" section above.

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


## **Running ANACIN-X**:

Use the 'comm_pattern_analysis.sh' script to generate traces of a selected communication pattern and perform analysis on the event graphs.  

**Important**: Make sure that the system you're running on supports the inputs you provide from the options below.  If you request that the system use more processes or nodes than are available, or if you select a different scheduler from what is available, the program will fail.

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
                Be sure that this is set to more than 1.  Otherwise, analysis will not work.
                (Default 2 executions)
* -o        : If used, allows the user to define their own path to 
                store output from the project. 
                Be sure to define an absolute path that can exist on your machine.
                Use a different path when running multiple times on the same settings to avoid overwriting.
                (Defaults to the directory '$HOME/comm_pattern_output')
* -nd       : Takes 3 arguments in decimal format (start percent, step size, end percent) to define message non-determinism percentages present in the final data.
                Start percent and end percent are the lowest and highest percentages used respectively.  The step size defines the percentages in between.
                For example, default values correspond to '-nd 0.0 0.1 1.0'. The percentages used from this are 0, 10, 20, 30, ..., 100. This is the recommended setting.
                All 3 values must fall between 0 and 1, inclusive, and must satisfy the relationship 'start percent + (step size * number of percentages used) = end percent'.
                (Defaults to starting percent of 0%, step size of 10%, and ending percent of 100%)
* -nt       : When running the unstructured mesh communication pattern, takes the percentage of topological non-determinism in decimal format.
                For example, default values correspond to '-nt 0.5'.
                Value must fall in the range of 0 to 1, inclusive.
                (Defaults to 50% topological non-determinism percentage)
* -c        : When running the unstructured mesh communication pattern, 
                use this with 3 arguments to define the grid coordinates. 
                The three values must be set so that their product equals the number of processes used.
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
                

If the project is run with settings that are small, then the communication pattern generated may end up not being non-deterministic.  A few things can be done to increase the odds of inducing non-determinism in a simulation:
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

### **Result Visualization**: 

There are two methods to do visualization of the kernel distance data from ANACIN-X.  We recommend using Jupyter Notebooks if you can pull it up from your machine.  If you can't use Jupyter notebooks on your machine, we provide a command line python tool to create a .png file for data visualization.  

In either case, we provide the user with sample KDTS data within the ANACIN-X project under the sub-directory 'sample_kdts'.  The user has the option to visualzie the provided sample results or to visualize their own generated results.  We describe each visualization method in more detail below:

#### Method 1 - Jupyter

If you can use Jupyter to visualize the data for the project, input the following command from the machine where you ran your copy of ANACIN-X:

```
jupyter notebook
```

Within Jupyter, find the file titled **visualization.ipynb** in the same directory as the script you used to produce your data (that is the root of your project).

By opening this visualization jupyter notebook and following the instructions within, you can visualize the kernel distance data.  If you complete the steps provided in the visualization jupyter notebook, you will also find a .png file generated in your file system where you ran the notebook from.

#### Method 2 - Command Line Visualization

If you can't use Jupyter to visualize the data, then we recommend using the command line python tool to generate the png images.  This will take a few key steps:

If you are generating visualizations from provided sample kdts data, then do the following steps:
1. Get the full path to the root of your ANACIN-X project. (It should be of the form '/home/<your_path>/ANACIN-X/')
2. Get the full path to the provided sample kdts file you're using. (It should be of the form '/home/<your_path>/ANACIN-X/sample_kdts/<kdts_file_name>')
3. Get the name of the communication pattern used from the name of the kdts file you're using. (The file name should be of the form samp_<communication pattern name>_kdts_<parameters used>.pkl)
4. The use the following command from the root project directory to generate a .png visualization for the provided data:

```
python3 anacin-x/event_graph_analysis/visualization/make_message_nd_plot.py [Path to 'kdts.pkl' file with file name] [The type of communication pattern you used] anacin-x/event_graph_analysis/graph_kernel_policies/wlst_5iters_logical_timestamp_label.json [The name of a file to store the visualization in (excluding the file type)] 0.0 0.1 1.0
```

If you are generating visualization for your own data, you will first need to identify the inputs to the visualization script.  These can be found in 2 ways.
1. The first way to find the inputs is to look at the last 7 lines printed to standard out from your run.  There you can find:
  * The path to your kernel distance (KDTS) data file.
  * The communication pattern used.
  * The path to your kernel config JSON file.
  * The three settings which define message non-determinism percentages: 'Starting Non-determinism Percentage', 'Non-determinism Percentage Step Size', and 'Ending Non-determinism Percentage'.
  * The percentage of topological non-determinism. (For unstructured mesh visualizations.)
2. The second way to find the inputs is to navigate to your output directory in the following way.
  * Navigate to the directory that your output was stored in from your run and save the full path including the file name of the json file stored there.
  * Open the run_config.txt file stored in that directory and save the name of the communication pattern as listed in the first line item.
  * Find your non-determinism percentage settings on the three lines titled 'Starting Non-determinism Percentage', 'Non-determinism Percentage Step Size', and 'Ending Non-determinism Percentage'. 
  * If you ran unstructured mesh, your topological non-determinism percentage can also be found in the run_config.txt file under the line 'Topological Non-determinism Percentage'.  Then exit the run_config.txt file.
  * Follow the output directory structure down based on the inputs you gave to set the project with until you find a file titled 'kdts.pkl' and save the full path to your 'kdts.pkl' file so that it can be used when calling the visualization script.

Once you've gathered the needed inputs, return to the project directory where you submitted jobs from.  From there, input the following command:

```
python3 anacin-x/event_graph_analysis/visualization/make_message_nd_plot.py [Path to 'kdts.pkl' file with file name] [The type of communication pattern you used] [Path to kernel json used to generate kdts file] [The name of a file to store the visualization in (excluding the file type)] [Lowest percentage of message non-determinism used in decimal format] [The message non-determinism percent step size in decimal format] [Highest percent of message non-determinism used in decimal format] [--nd_neighbor_fraction <topological non-determinism percent in decimal format> (only used for unstructured mesh communication pattern)]
```

A png file will be produced and placed in the working directory if no absolute path is given for output or in the absolute path provided as an output file.  Note that there's no need to include the file type (.png) at the end of your output file name, as it will be attached automatically.

If you're doing your work and producing visualizations on a remote machine, remember to copy your png image to your local machine using a tool like scp to view the image.

### Supported Systems:

Currently, the software supports the following types of scheduler systems for job submission.  Make sure that you are running on one of these:
* LSF scheduled systems (ex. Tellico)
* Slurm scheduled systems (ex. Stampede2)
* Unscheduled systems (ex. Jetstream, personal computers)

**Important**: Please refer to the list of command line switches above to determine what settings you can configure.  If your system cannot support the settings requested, then you will need to change them.  The program will not run correctly if you request more processes or nodes than are available in your computer.


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

D. Chapp, N. Tan, S. Bhowmick, and M. Taufer. **Identifying Degrees and Sources of Non-Determinism in MPI Applications via Graph Kernels.** *Journal of IEEE Transactions on Parallel and Distributed Systems (IEEE TPDS)*, (2021).

D. Chapp, D. Rorabaugh, K. Sato, D. Ahn, and M. Taufer. **A Three-phase Workflow for General and Expressive Representations of Nondeterminism in HPC Applications.** *International Journal of High-Performance Computing Applications(IJHPCA), 1175-1184* (2019).

D. Chapp, K. Sato, D. Ahn, and M. Taufer. **Record-and-Replay Techniques for HPC Systems: A survey.** *Journal of Supercomputing Frontiers and Innovations, 5(1):11-30.* (2018).

D. Chapp, T. Johnston, and M. Taufer. **On the Need for Reproducible Numerical Accuracy through Intelligent Runtime Selection of Reduction Algorithms at the Extreme Scale.** *In Proceedings of IEEE Cluster Conference, pp. 166 – 175. Chicago, Illinois, USA.* September 8 – 11, 2015.

## Copyright and License:

Copyright (c) 2021, Global Computing Lab

ANACIN-X is distributed under terms of the [Apache License, Version 2.0](http://www.apache.org/licenses/LICENSE-2.0) with LLVM Exceptions.

See [LICENSE](https://github.com/TauferLab/ANACIN-X/blob/master/LICENSE) for more details.



