<p align="center">
    <img src="anacin_pngs/anacin-logo.png" width="350">
</p>

# ANACIN-X

[![DOI](https://zenodo.org/badge/364344863.svg)](https://zenodo.org/badge/latestdoi/364344863)
[![Open in Code Ocean](https://codeocean.com/codeocean-assets/badge/open-in-code-ocean.svg)](https://doi.org/10.24433/CO.2809639.v1)

## Introduction

Non-deterministic results often arise unexpectedly in High Performance Computing (HPC) applications.  These make reproducible and correct results difficult to create.  As such, there is a need to improve the ability of software developers and scientists to comprehend root sources of non-determinism in their applications.  To this end, we present ANACIN-X.

This repository contains a suite of tools for trace-based analysis of non-deterministic behavior in MPI applications. The core components of this tool suite are as follows.  
* A Framework for Characterizing Root Sources of Non-Determinism as Graph Similarity: This is broken down into the following stages
  1. Execution Trace Collection
  2. Event Graph Construction
  3. Event Graph Kernel Analysis
  4. Kernel Distance Visualization
* Use Case Communication Patterns

The best way to learn more details on how ANACIN-X works is to see either the [Software Overview](https://github.com/TauferLab/ANACIN-X/wiki/Software-Overview) page on the ANACIN-X wiki or review the [publications](#publications) listed at the bottom of this README.

This document is organized in the following order:
* [Building ANACIN-X](#building-anacin-x)
* [Running ANACIN-X](#running-anacin-x)
  * [Running ANACIN-X on a Benchmark Application](#running-anacin-x-on-a-benchmark-application)
  * [Running ANACIN-X on an External Application](#running-anacin-x-on-an-external-application)
* [Visualization Results](#result-visualization)
  * [Visualizing Benchmark Application Data](#visualizing-benchmark-application-data)
  * [Visualizing External Application Data](#visualizing-external-application-data)
* [Reproducting Published Results](#reproducting-published-results)
* Additional Project Details
  1. [The project team](#project-team)
  2. [Publications associated with the software](#publications)
  3. [Copyright and license information](#copyright-and-license)


## **Building ANACIN-X**

Here, we outline the procedure to install ANACIN-X and its dependencies.  

For more details about the information in this section, please see the [wiki page on 'Installation'](https://github.com/TauferLab/ANACIN-X/wiki/Installation).  A complete list of software dependencies for ANACIN-X can be found at the ['Dependencies' wiki page](https://github.com/TauferLab/ANACIN-X/wiki/Dependencies).

**We strongly recommend installing the Spack and Conda package managers before installing ANACIN-X**.  We use these to help automate the installation of dependencies.

### ANACIN-X:

Once you have cloned the ANACIN-X repository to your local machine, be sure to enter the project root for setup.

If you're using the  [Jetstream cloud computer](https://jetstream-cloud.org) image for Anacin-X titled ["Ubuntu20.04_Anacin-X"](https://use.jetstream-cloud.org/application/images/1056), you can skip this next command.  Otherwise, we strongly recommend installing the dependencies for the project with the following command.  

If you will use this command to install dependencies, be sure to have the Spack and Conda package managers set up beforehand.  If there is a specific C compiler that you wish to use on your machine, please see the ['Special Case' section](https://github.com/TauferLab/ANACIN-X/wiki/Installation#special-case) of the ANACIN-X wiki.

```
. setup_deps.sh
``` 

Follow the prompts at the beginning, and then the installation will run on its own.  The installation of dependencies may take some time to complete.

Assuming all dependenices are installed and loaded, build ANACIN-X and its submodules by running

```
. setup.sh -c
```

If you do not wish to build ANACIN-X with callstack tracing functionality, remove the '-c' in the above command.


## **Running ANACIN-X**:

For more details on running ANACIN-X than what can be found in this README, see the ['Running ANACIN-X'](https://github.com/TauferLab/ANACIN-X/wiki/Running-ANACIN-X) wiki page.

ANACIN-X must be run alongside another application.  There are 2 categories of this.
* Run ANACIN-X with one of three benchmark applications packaged within this repository.
* Run ANACIN-X with an external application (e.g., a user defined communication pattern such as MiniAMR or MCB Grid).

### Running ANACIN-X on a Benchmark Application

Use the 'comm\_pattern\_analysis.sh' script to generate traces of a selected benchmark communication pattern and perform analysis on the event graphs.

The following command line switches can be used to define parameters for your job submission.  More details for each, such as constraints and default values, can be found in the [ANACIN-X wiki](https://github.com/TauferLab/ANACIN-X/wiki/Running-ANACIN-X#running-anacin-x-with-a-benchmark-application)
* -p        : Defines the size of the mpi communicator (number of MPI processes)
* -i        : Defines the number of times a benchmark communication pattern appears in a single execution of ANACIN-X. 
* -s        : The size in bytes of the messages passed when generating communication patterns.
* -n        : The number of compute nodes requested for running the ANACIN-X workflow. 
* -r        : The number of runs to make of the ANACIN-X workflow.
* -cp       : Used to define the communication pattern benchmark for testing. (i.e., message_race, amg2013, or unstructured_mesh)
* -sc       : Used to define which schedule system is currently in use. (i.e., lsf, slurm, or unscheduled)
* -ct       : Used to define which backtracing tool should be used during callstack tracing. (i.e., glibc or libunwind)
* -o        : Used to define a custom path to store output from the project. 
* -nd       : Takes 3 arguments in decimal format (start percent, step size, end percent) to define message non-determinism percentages present in the final data.
* -nt       : When running the unstructured mesh communication pattern, takes the percentage of topological non-determinism in decimal format.
* -c        : When running the unstructured mesh communication pattern, takes 3 arguments (integers greater than 1) to define the grid coordinates.
* -v        : If used, will display the execution settings prior to running the execution.
* -h        : Used to display the list of switch options.

If you're running on a system that uses the Slurm scheduler, then the following switches can be used to define settings for job submission:
* -q        : Defines the queue to submit scheduled jobs to. (Defaults to the "normal" queue)
* -t        : A maximum time limit in minutes on the time provided to jobs submitted. (Default 10 minutes)
                

If the project is run with settings that are small, then the communication pattern generated may end up not being non-deterministic.  A few things can be done to increase the odds of inducing non-determinism in a simulation:
* It is good to run on a large number of processes (at least 10) and a large number of runs (at least 50) to increase the odds of non-determinism arising.
* By running a communication pattern with multiple iterations (using the -i flag), the user can cause more non-determinism.  This is particularly important when running the message race communication pattern.
* Running with a small message size (using the -s flag) can increase the likelihood of non-determinism.
* Running the program across multiple compute nodes (using the -n flag) can help to cause more non-determinism.

Below is an example run of the script as one might submit it to run message\_race on an unscheduled system.

```
. ./comm_pattern_analysis.sh -p 20 -i 10 -n 1 -v -r 100 -sc unscheduled -cp message_race -o $HOME/message_race_sim_1
```

Below is another example run of the script as one might submit it on the Stampede2 cluster computer to analyze the AMG 2013 communication pattern:

```
. ./comm_pattern_analysis.sh -p 48 -n 2 -v -r 50 -sq "skx-normal" -sc slurm -cp amg2013 -o $WORK2/anacinx_output_1
```

Be sure to check that the settings you run with will work on the system you use.  If you request too many resources or too many jobs, the code may error out.

### Running ANACIN-X on an External Application

If you're running ANACIN-X with an external application, you will need to run the stages of it individually.  We will outline here how to run the stages:
* [Execution Trace Collection](#execution-trace-collection)
* [Event Graph Construction](#event-graph-construction)
* [Event Graph Kernel Analysis](#event-graph-kernel-analysis)

For more details about running these sections, please see the wiki page section on ['Running ANACIN-X with an External Application'](https://github.com/TauferLab/ANACIN-X/wiki/Running-ANACIN-X#running-anacin-x-with-an-external-application).

Be sure to install all dependencies listed in the ['Dependencies'](https://github.com/TauferLab/ANACIN-X/wiki/Dependencies) wiki page, or use the automated dependency installation described in the ['Building ANACIN-X'](#building-anacin-x) section above, prior to running the stages. 

#### Execution Trace Collection

Be sure to configure and link all the PMPI tools prior to tracing.  See their respective GitHub pages linked in the ['Dependencies'](https://github.com/TauferLab/ANACIN-X/wiki/Dependencies) wiki page for more details on configuration.  PnMPI will need to be configured to use the linked modules.  See the PnMPI [GitHub page](https://github.com/LLNL/PnMPI/tree/f6fcc801ab9305352c510420c6439b7d48a248dc) for more information on linking software and configuring PnMPI.

The command to trace your application will look something like:

```
LD_PRELOAD=<path to libpnmpi.so> PNMPI_LIB_PATH=<path to pnmpi linking directory> PNMPI_CONF=<path to pnmpi configuration directory> mpirun -np [number of MPI processes requested] [application executable to be traced] [arguments to traced application]
```

You will need to run the above command many times to produce a sample of traces.  The traces across runs will be compared in subsequent stages.  

Be sure to configure each of the PMPI tools to store their output for a single run in the same directory.  We will call it a 'run directory'.  Suppose you make 100 runs of your application.  There should then be 100 'run directories' adjacent to each other, each one storing all the trace files from a run.

#### Event Graph Construction

Please see the dumpi_to_graph [GitHub page](https://github.com/TauferLab/dumpi_to_graph/tree/3966d25a916ddf0cd5e4e71ce71702798c0f39e1) to create a configuration file for your needs, using the examples that dumpi_to_graph provides as a reference.

Once you have configured dumpi_to_graph, use a command of the following form to construct an event graph from the traces within one run directory.

```
mpirun -np [number of MPI processes requested] [executable file for dumpi_to_graph found in its build directory] [configuration file for dumpi_to_graph found in its config directory] [path to a trace file directory (i.e., a run directory)]
```

An automation file titled 'build_graph.sh' is provided within the 'anacin-x/workflow_scripts' directory to implement the above command.  The build_graph.sh script must take as arguments all 4 of the arguments listed in the above command in the order they appear.

The above command must be run for each run directory.  An event graph will be stored in each run directory that the above command is used on.

#### Event Graph Kernel Analysis

First select a slicing policy file from the 'anacin-x/event_graph_analysis/slicing_policies' directory.  Each one will break the graph up into components based on different functions or data and may be relevant to different applications.  If your application uses barriers, we recommend using one of the slicing policy files with 'barrier_delimited_' in the title.

Once you have decided on a slicing policy to use, run the following command to perform slice extraction for each event graph.

```
mpirun -np [number of MPI processes requested] anacin-x/event_graph_analysis/extract_slice.py [full path to event graph from one run] [full path to slicing policy file] -o "slices"
```

An automation file titled 'extract_slices.sh' is provided within the 'anacin-x/workflow_scripts' directory to implement the above command.  The extract_slices.sh script must take as arguments all 4 of the arguments listed in the above command in the order they appear.

To run event graph kernel calculations, first select a graph kernel policy file 'anacin-x/event_graph_analysis/graph_kernel_policies' directory.  We suggest using the file 'wlst_5iters_logical_timestamp_label.json'.

Then run the following command to generate kernel distance data.

```
mpirun -np [number of MPI processes requested] anacin-x/event_graph_analysis/compute_kernel_distance_time_series.py [directory storing each run directory] [full path to graph kernel policy file] --slicing_policy [full path to slicing policy file] -o "kdts.pkl" --slice_dir_name "slices" [-c (only to be used if you traced your application with CSMPI to collect callstack data)]
```

Unlike the previous stages of the workflow, the kernel calculation command above only takes place once for all runs of the traced application.

## **Result Visualization**: 

For more details on visualizing ANACIN-X data beyond what is described here, see the ['Visualization'](https://github.com/TauferLab/ANACIN-X/wiki/Visualization) wiki page.

For demonstration purposes, we provide the user with sample KDTS data within the ANACIN-X project under the sub-directory 'sample_kdts'.  The user has the option to visualzie the provided sample results or to visualize their own generated results.  Note that callstack visualization will not work for sample data.  Commands for running sample data can be found in the section below on ['Visualizing Benchmark Application Data'](#visualizing-benchmark-application-data).

### Visualizing Benchmark Application Data

Throughout this, you can view the ANACIN-X wiki section on ['Benchmark Application Data Visualization'](https://github.com/TauferLab/ANACIN-X/wiki/Visualization#benchmark-application-data-visualization) for more information on locating what arguments to pass to visualization scripts and on what they output.

If you have access to Jupyter Notebooks, you can visualize kernel distance and callstack data using the Jupyter Notebook titled 'visualization.ipynb'.  Open it and follow the prompts to generate your figures.

If you will visualize provided sample kernel distance data, run the following command from the root of your project.

```
python3 anacin-x/event_graph_analysis/visualization/make_message_nd_plot.py [Path to 'kdts.pkl' file with file name] [The type of communication pattern you used] anacin-x/event_graph_analysis/graph_kernel_policies/wlst_5iters_logical_timestamp_label.json [The name of a file to store the visualization in (excluding the file type)] 0.0 0.1 1.0
```

If you will visualize kernel distance data from a benchmark application using the command line, run the following command from the root of your project.

```
python3 anacin-x/event_graph_analysis/visualization/make_message_nd_plot.py [Path to 'kdts.pkl' file with file name] [The type of communication pattern you used] [Path to kernel json used to generate kdts file] [The name of a file to store the visualization in (excluding the file type)] [Lowest percentage of message non-determinism used in decimal format] [The message non-determinism percent step size in decimal format] [Highest percent of message non-determinism used in decimal format] [--nd_neighbor_fraction <topological non-determinism percent in decimal format> (only used for unstructured mesh communication pattern)]
```

If you will visualize callstack data from a benchmark application using the command line, run the following commands from the root of your project.

**Important**: In the second command below, the file apps/comm\_pattern\_generator/build/comm\_pattern\_generator is an executable file for your project.  Be sure that you run the below commands on KDTS data that was generated from the same executable file as what you input below!

```
python3 anacin-x/event_graph_analysis/anomaly_detection.py [Path to 'kdts.pkl' file with file name] anacin-x/event_graph_analysis/anomaly_detection_policies/all.json -o flagged_indices.pkl

python3 anacin-x/event_graph_analysis/callstack_analysis.py ['flagged_indices.pkl file name with same path as 'kdts.pkl'] [Path to 'kdts.pkl' file with file name] apps/comm_pattern_generator/build/comm_pattern_generator

python3 anacin-x/event_graph_analysis/visualization/visualize_callstack_report.py ['non_anomaly_report_for_policy_all.txt' file name with same path as 'kdts.pkl'] --plot_type="bar_chart"
```

### Visualizing External Application Data
	
If you're visualizing data from an external application (i.e., not one of the provided three benchmark applications), use the following collection of commands to visualize data.

If you're generating a kdts visualization, run the following command from within the directory 'anacin-x/event_graph_analysis'.

```
python3 visualization/visualize_kernel_distance_time_series.py [Path to 'kdts.pkl' file with file name. This can be found in the directory that stores all your run directories.] --plot_type=box
```

This will create the visualization file titled 'kernel_distance_time_series.png' within the directory you're currently in.

If you're visualizing callstack data, do so with the following commands from within the root directory of your project.

```
python3 anacin-x/event_graph_analysis/anomaly_detection.py [Path to 'kdts.pkl' file with file name] anacin-x/event_graph_analysis/anomaly_detection_policies/all.json -o flagged_indices.pkl

python3 anacin-x/event_graph_analysis/callstack_analysis.py ['flagged_indices.pkl file name with same path as 'kdts.pkl'] [Path to 'kdts.pkl' file with file name] [path to executable filed used during tracing (must be the exact same file without being recompiled!)]

python3 anacin-x/event_graph_analysis/visualization/visualize_callstack_report.py ['non_anomaly_report_for_policy_all.txt' file name with same path as 'kdts.pkl'] --plot_type="bar_chart"
```

## Reproducing Published Results

Visualization methods like those described above can be used to produce figures like those in the publications listed in the [publications](#publications) section below, particularly the paper "[Identifying Degrees and Sources of Non-Determinism in MPI Applications via Graph Kernels.](https://ieeexplore.ieee.org/abstract/document/9435018)".  If the user has access to the applications miniAMR and MCB, such visualizations can be reproduced in the following manners.

1. For Figure 17, corresponding to visualizations of the kernel distance time series for MCB, run the kdts visualization script in the visualization section above for external applications. (i.e., use the 'visualize_kernel_distance_time_series.py' script)
2. For Figure 14, corresponding to visualization of callstacks from the miniAMR tool, run the callstack visualization script for external applications. (i.e., use the 'visualize_callstack_report.py' script in the manner outlined above)
3. For Figure 13, corresponding to visualization of kernel distances across different miniAMR time steps, the 'visualize_kernel_distance_time_series.py' script can also be used, but must be accompanied by 'application events' specific to miniAMR.  For miniAMR, these application events correspond to the number of blocks transferred per mesh refinement in a pickle file format.  This is seen in the line showing the '# of Blocks Transferred per Mesh Refinement' in the referenced figure.  The following command shows how to pass these application events into the visualization script.

```
python3 visualization/visualize_kernel_distance_time_series.py [Path to 'kdts.pkl' file with file name. This can be found in the directory that stores all your run directories.] --plot_type=box --application_events=blocks_transferred.pkl
```

To reproduce visualizations like those displayed in the publication "[ANACIN-X: A Software Framework for Studying Non-determinism in MPI Applications.](https://www.sciencedirect.com/science/article/pii/S2665963821000634)", see the ANACIN-X Code Ocean repository [here](https://codeocean.com/capsule/0309009/tree/v3)


## Project Team

Developers:
* Nick Bell
* Dylan Chapp
* Kae Suarez
* Nigel Tan

Project Advisors:
* Dr. Sanjukta Bhowmick
* Dr. Michela Taufer (Project Lead)

## Publications
	
Patrick Bell, Kae Suarez, Dylan Chapp, Nigel Tan, Sanjukta Bhowmick, and Michela Taufer. **ANACIN-X: A Software Framework for Studying Non-determinism in MPI Applications.** *Software Impacts, 10:100151*, (2021).

D. Chapp, N. Tan, S. Bhowmick, and M. Taufer. **Identifying Degrees and Sources of Non-Determinism in MPI Applications via Graph Kernels.** *Journal of IEEE Transactions on Parallel and Distributed Systems (IEEE TPDS)*, (2021).

D. Chapp, D. Rorabaugh, K. Sato, D. Ahn, and M. Taufer. **A Three-phase Workflow for General and Expressive Representations of Nondeterminism in HPC Applications.** *International Journal of High-Performance Computing Applications(IJHPCA), 1175-1184* (2019).

D. Chapp, K. Sato, D. Ahn, and M. Taufer. **Record-and-Replay Techniques for HPC Systems: A survey.** *Journal of Supercomputing Frontiers and Innovations, 5(1):11-30.* (2018).

D. Chapp, T. Johnston, and M. Taufer. **On the Need for Reproducible Numerical Accuracy through Intelligent Runtime Selection of Reduction Algorithms at the Extreme Scale.** *In Proceedings of IEEE Cluster Conference, pp. 166 – 175. Chicago, Illinois, USA.* September 8 – 11, 2015.

## Copyright and License

Copyright (c) 2021, Global Computing Lab

ANACIN-X is distributed under terms of the [Apache License, Version 2.0](http://www.apache.org/licenses/LICENSE-2.0) with LLVM Exceptions.

See [LICENSE](https://github.com/TauferLab/ANACIN-X/blob/master/LICENSE) for more details.



