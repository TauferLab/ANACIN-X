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


## **Building ANACIN-X**

**Important**: Please read the instructions in this README in order.  Effective use of this software is dependent on correct installation of all dependencies.  Since there are a collection of dependencies, we provide tools for automating the process.  So read through the instructions carefully.

If you're running your version of the project on an instance of the [Jetstream cloud computer](https://jetstream-cloud.org), use the image ["Ubuntu20.04_Anacin-X"](https://use.jetstream-cloud.org/application/images/1056) and skip ahead to the subsection below about installing ANACIN-X.  If you're using a different Jetstream image or if you're not using Jetstream, continue reading here to ensure all dependencies get installed.

**If you haven't already, you will need to install the Spack and Conda package managers**, be sure to do so using the following instructions.  We will use these to help automate the installation of dependencies.

### Spack:
Spack is a package manager with good support for scientific/HPC software. To use Spack you will need Python. We recommend you install Spack *and* enable Spack's shell integration. 

To install Spack, follow the instructions at: [Spack Install](https://spack.readthedocs.io/en/latest/getting_started.html)

In particular, make sure to follow the instructions under "Shell support". This step will allow software installed with Spack to be loaded and unloaded as [environment modules.](https://spack.readthedocs.io/en/latest/getting_started.html#installenvironmentmodules) 

### Conda:
Conda is a cross-language package, dependency, and environment manager. We use Conda to manage the dependencies of ANACIN-X's Python code.  We recommend using the Anaconda installation of the package manager rather than the Miniconda version so that you can have Jupyter installed on your machine for data visualization.

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

Assuming all dependenices are installed and loaded, you will build all of ANACIN-X's components by running

```
. setup.sh -c
```

If you do not wish to build ANACIN-X with callstack tracing functionality, remove the '-c' in the above command.

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
* [Pluto](https://github.com/TauferLab/Pluto/tree/main)
* [dumpi_to_graph](https://github.com/TauferLab/dumpi_to_graph/tree/3966d25a916ddf0cd5e4e71ce71702798c0f39e1)
* [CSMPI](https://github.com/TauferLab/CSMPI/tree/367a1c3bdba1511ad5d415daecf714ea01c536c6)


## **Running ANACIN-X**:

ANACIN-X must be run alongside another application.  There are 2 categories of this.
* Firstly, for demonstration purposes, ANACIN-X comes packaged with 3 non-deterministic benchmark applications to analyze. These benchmark applications are accompanied by automation scripts to simplify the process of running ANACIN-X with them. See the section below for options.
* Secondly, for running ANACIN-X with an external application (e.g., a user defined communication pattern such as MiniAMR or MCB Grid), we will describe the procedure for running the ANACIN-X framework.

### Running ANACIN-X with Benchmark Applications

Use the 'comm\_pattern\_analysis.sh' script to generate traces of a selected benchmark communication pattern and perform analysis on the event graphs.  

**Important**: Make sure that the system you're running on supports the inputs you provide from the options below.  If you request that the system use more processes or nodes than are available, or if you select a different scheduler from what is available, the program will fail.

**Note**: If you come across any errors while running your code, be sure to make sure that your version of the code is up to date using git commands like 'git pull'.

The following command line switches can be used to define parameters for your job submission:
* -p        : Defines the size of the mpi communicator (number of MPI processes)
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
* -cp      : Used to define the communication pattern benchmark for testing. 
                Must be one of the 3 provided benchmarks in the following format: message_race, amg2013, or unstructured_mesh.
* -sc      : Used to define which schedule system is currently in use.
                Must be one of the following options: lsf, slurm, or unscheduled.
* -ct      : Used to define which backtracing tool should be used during callstack tracing.
	        Must be one of the following options: glibc or libunwind.
	        (Defaults to glibc)
		Note that if this is changed from default, then CSMPI will need to be built with the corresponding library.  Instructions are at the CSMPI github repository.
* -o        : If used, allows the user to define their own path to 
                store output from the project. 
                Be sure to define an absolute path that can exist on your machine.
                Use a different path when running multiple times on the same settings to avoid overwriting.
                (Defaults to the directory '$HOME/comm_pattern_output')
* -nd       : Takes 3 arguments in decimal format (start percent, step size, end percent) to define message non-determinism percentages present in the final data.
                Start percent and end percent are the lowest and highest percentages used respectively.  The step size defines the percentages in between.
                For example, default values correspond to '-nd 0.0 0.1 1.0'. The percentages used from this are 0, 10, 20, 30, ..., 100. This is the recommended setting.
                All 3 values must fall between 0 and 1, inclusive, and must satisfy the relationship 'start percent + (step size * number of percentages used) = end percent'.
		All 3 values must also contain no more than 2 digits past the decimal. (i.e. corresponding to integer percentages)
                (Defaults to starting percent of 0%, step size of 10%, and ending percent of 100%)
* -nt       : When running the unstructured mesh communication pattern, takes the percentage of topological non-determinism in decimal format.
                For example, default values correspond to '-nt 0.5'.
                Value must fall in the range of 0 to 1, inclusive.
                (Defaults to 50% topological non-determinism percentage)
* -c        : When running the unstructured mesh communication pattern, 
                use this with 3 arguments (integers greater than 1) to define the grid coordinates. 
                The three values must be set so that their product equals the number of processes used.
                (Ex. -c 2 3 4)
* -v        : If used, will display the execution settings prior 
                to running the execution.
* -h        : Used to display the list of switch options.

If you're running on a system that uses the Slurm scheduler, then the following switches can be used to define settings for job submission:
* -q       : Defines the queue to submit scheduled jobs to. 
                (Defaults to the "normal" queue)
* -t        : A maximum time limit in minutes on the time provided to jobs submitted. 
                (Default 10 minutes)
                

If the project is run with settings that are small, then the communication pattern generated may end up not being non-deterministic.  A few things can be done to increase the odds of inducing non-determinism in a simulation:
* It is good to run on a large number of processes (at least 10) and a large number of runs (at least 50) to increase the odds of non-determinism arising.
* By running a communication pattern with multiple iterations (using the -i flag), the user can cause more non-determinism.  This is particularly important when running the message race communication pattern.
* Running with a small message size (using the -s flag) can increase the likelihood of non-determinism.
* Running the program across multiple compute nodes (using the -n flag) can help to cause more non-determinism.

Below is an example run of the script as one might submit it to run message\_race on an unscheduled system.

```
. ./comm_pattern_analysis.sh -p 20 -i 10 -v -r 100 -o $HOME/message_race_sim_1
```

Below is another example run of the script as one might submit it on the Stampede2 cluster computer:

```
. ./comm_pattern_analysis.sh -p 48 -n 2 -v -r 50 -sq "skx-normal" -o $WORK2/anacinx_output_1
```

If a communication pattern or a scheduler type has not been provided to the script using one of command line switches above, follow the prompts at the beginning of the script to select them.  You will need to input a communication pattern to generate and which scheduler your computing system employs.  You can choose between any of the communication patterns listed in the supported settings section below with these corresponding formats: message_race, amg2013, unstructured_mesh.  And you can choose one of the following scheduler systems: lsf, slurm, unscheduled.

Be aware that if you run the project on some machines and some job queues, there will be a limit to the number of jobs that can be submitted.  In such cases, you may lose some jobs if you try to run the program with settings that produce more jobs than are allowed in the queue being used.

### Running ANACIN-X with an External Application

As described in the software overview at the top of this README, there are 3 major stages of the ANACIN-X framework prior to visualization.  We will describe how to use each of these.  As a reminder, the three stages are:
* Execution Trace Collection
* Event Graph Construction
* Event Grph Kernel Analysis

Be sure to install all dependencies listed in the 'Dependencies' section above prior to running the stages. 

#### Execution Trace Collection

In this stage of the ANACIN-X framework, you will trace an input application using a 'stack' of MPI profiling interface (PMPI) tools.  Specifically, you will trace the application using the following tools:
* [sst-dumpi](https://github.com/TauferLab/sst-dumpi/tree/b47bb77ccbe3b87d585e3701e1a5c2f8d3626176)
* [Pluto](https://github.com/TauferLab/Pluto/tree/main)
* [CSMPI](https://github.com/TauferLab/CSMPI/tree/367a1c3bdba1511ad5d415daecf714ea01c536c6) (CSMPI is optional for the purpose of visualizing kernel distance data, but is required to visualize callstack data.)

To 'stack' the above software tools, use the interface [PnMPI](https://github.com/LLNL/PnMPI/tree/f6fcc801ab9305352c510420c6439b7d48a248dc), open-source, MPI tool infrastructure that builds on top of the standardized PMPI interface.

Be sure to configure all the PMPI tools prior to tracing.  And be sure to link the PMPI tools using PnMPI prior to tracing.  See their respective GitHub pages linked above for more details.  PnMPI will need to be configured to use the linked modules.  See the PnMPI [GitHub page](https://github.com/LLNL/PnMPI/tree/f6fcc801ab9305352c510420c6439b7d48a248dc) for more information on linking software and configuring PnMPI.

Your command to trace your application will likely look something of the form:

```
LD_PRELOAD=<path to libpnmpi.so> PNMPI_LIB_PATH=<path to pnmpi linking directory> PNMPI_CONF=<path to pnmpi configuration directory> mpirun -np [number of processes] [application executable to be traced] [arguments to traced application]
```

You will need to run the above command many times to produce a sample of traces.  The traces across runs will be compared in subsequent stages.  

Be sure to configure each of the PMPI tools to store their output for a single run in the same directory.  We will call it a 'run directory'.  Suppose you make 100 runs of your application.  There should then be 100 'run directories' adjacent to each other, each one storing all the trace files from a run.

#### Event Graph Construction

Once you have generated a set of traces for a given application, the traces must be used to generate 'event graphs' for the purpose of analysis.  We use the [dumpi_to_graph](https://github.com/TauferLab/dumpi_to_graph/tree/3966d25a916ddf0cd5e4e71ce71702798c0f39e1) software tool to convert traces into event graphs.

Dumpi_to_graph must be configured prior to use.  Please see the dumpi_to_graph [GitHub page](https://github.com/TauferLab/dumpi_to_graph/tree/3966d25a916ddf0cd5e4e71ce71702798c0f39e1) to create a configuration file for your needs, using the examples that dumpi_to_graph provides as a reference.  For ease of use, store any configuration files you create within dumpi_to_graph's config directory.

Use a command of the following form to construct an event graph from the traces within one run directory.  Note that dumpi_to_graph is designed to be parallelized using MPI.

```
mpirun -np [number of MPI processes requested] [executable file for dumpi_to_graph found in its build directory] [configuration file for dumpi_to_graph found in its config directory] [path to a trace file directory (i.e., a run directory)]
```

An automation file titled 'build_graph.sh' is provided within the 'anacin-x/workflow_scripts' directory to implement the above command.  The build_graph.sh script must take as arguments all 4 of the arguments listed in the above command in the order they appear.

The above command must be run for each run directory.  An event graph will be stored in each run directory that the above command is used on.  Then the event graphs can be compared in the next stage of ANACIN-X.

#### Event Graph Kernel Analysis

Event graph kernel analysis is composed of two parts:
1. Event graph slice extraction
2. Event graph kernel calculations

The first of these, slice extraction, requires the use of a policy file to define where to start and stop slices of a graph.  Policy files are provided and can be found within the 'anacin-x/event_graph_analysis/slicing_policies' directory.  Each one will break the graph up into components based on different functions or data and may be relevant to different applications.  If your application uses barriers, we recommend using one of the slicing policy files with 'barrier_delimited_' in the title.

Event graph slice extraction must take place for each event graph.  Once you have decided on a slicing policy to use, run the following command for each event graph using the extract slices script 'anacin-x/event_graph_analysis/extract_slice.py'.  Note that this script is parallelized using mpi4py.

```
mpirun -np [number of MPI processes requested] [full path to extract_slices.py script] [full path to event graph from one run] [full path to slicing policy file] -o "slices"
```

An automation file titled 'extract_slices.sh' is provided within the 'anacin-x/workflow_scripts' directory to implement the above command.  The extract_slices.sh script must take as arguments all 4 of the arguments listed in the above command in the order they appear.

After slice extraction is complete for all event graphs, the final step to creating kernel distance data is kernel calculations on the event graph slices.

To perform kernel calculations, use the 'compute_kernel_distance_time_series.py' script within the 'anacin-x/event_graph_analysis' directory.  Note that this script is parallelized using mpi4py.

To run this script, you will need to select a graph kernel policy file.  We suggest using the file 'anacin-x/event_graph_analysis/wlst_5iters_logical_timestamp_label.json' because it is the most well tested with the workflow.  This file corresponds to running the Weisfeiller-Lehmann subtree (WLST) graph kernel with 5 iterations and the logical timestamp for vertex label data.  More information about this kernel can be found in the paper ["Weisfeiller-lehmann graph kernels"](https://www.jmlr.org/papers/volume12/shervashidze11a/shervashidze11a.pdf).  See the file 'wlst_sweep_vertex_labels.json' within the same directory as the recommended kernel file for examples of other vertex labels to use with the WLST kernel.  You can change the graph kernel file to fit what is best for your project.

Finally, run the following command to generate kernel distance data.

```
mpirun -np [number of MPI processes requested] [full path to compute_kernel_distance_time_series.py script] [directory storing each run directory] [full path to graph kernel policy file] --slicing_policy [full path to slicing policy file] -o "kdts.pkl" --slice_dir_name "slices" [-c (only to be used if you traced your application with CSMPI to collect callstack data)]
```

Unlike the previous stages of the workflow, the kernel calculation command above only takes place once for all runs of the traced application.

### **Result Visualization**: 

There are two methods to visualize kernel distance data from ANACIN-X that corresponds to one of the three provided benchmark applications.  We recommend using Jupyter Notebooks if you can pull it up from your machine.  If you can't use Jupyter notebooks on your machine, we provide 2 command line python tools to: (1) create a .png file for visualization of the relationship between kernel distance and percentage of message non-determinism, or kdts visualizations and (2) create a bar chart of of which callstack functions presented the highest impact on kernel distance during an applications runtime, or callstack visualizations.  

If you are visualizing data that corresponds to an external application (i.e., you did not use the 'comm_pattern_analysis.sh' script to generate data), we provide a command line python tool that visualizes how the kernel distance changes across slices of an applications execution.  Read below the 'Command Line Visualization' section for details.

In either case, we provide the user with sample KDTS data within the ANACIN-X project under the sub-directory 'sample_kdts'.  The user has the option to visualzie the provided sample results or to visualize their own generated results.  We describe each visualization method in more detail below.

#### Method 1 - Jupyter

If you can use Jupyter to visualize the data for the project and you generated data from one of the three provided benchmark applications, input the following command from the machine where you ran your copy of ANACIN-X:

```
jupyter notebook
```

Within Jupyter, find the file titled **visualization.ipynb** in the same directory as the script you used to produce your data (that is the root of your project).

By opening this visualization jupyter notebook and following the instructions within, you can visualize the kernel distance data.  If you complete the steps provided in the visualization jupyter notebook, you will also find a .png file generated in your file system where you ran the notebook from.

#### Method 2 - Command Line Visualization

If you can't use Jupyter to visualize the data, then we recommend using the command line python tool to generate the png images.  This will take a few key steps:

If you are generating a kdts visualization for your own data, you will first need to identify the inputs to the visualization script.  These can be found in 2 ways.
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

If you are generating a kdts visualization from provided sample kdts data, then do the following steps:
1. Get the full path to the root of your ANACIN-X project. (It should be of the form '/home/<your_path>/ANACIN-X/')
2. Get the full path to the provided sample kdts file you're using. (It should be of the form '/home/<your\_path>/ANACIN-X/sample\_kdts/<kdts_file_name>')
3. Get the name of the communication pattern used from the name of the kdts file you're using. (The file name should be of the form samp\_<communication pattern name>\_kdts\_<parameters used>.pkl)
4. Then use the following command from the root project directory to generate a .png visualization for the provided data.

```
python3 anacin-x/event_graph_analysis/visualization/make_message_nd_plot.py [Path to 'kdts.pkl' file with file name] [The type of communication pattern you used] anacin-x/event_graph_analysis/graph_kernel_policies/wlst_5iters_logical_timestamp_label.json [The name of a file to store the visualization in (excluding the file type)] 0.0 0.1 1.0
```

A png file that visualizes the relationship between kernel distance and percentage of message non-determinism in your communication pattern will be produced and placed in the working directory if no absolute path is given for output or in the absolute path provided as an output file.  Note that there's no need to include the file type (.png) at the end of your output file name, as it will be attached automatically.

If you are generating a callstack visualization, you will need to input the following sequence of commands from within your project directory.

**Note**, if you are creating visualizations from sample data provided within ANACIN-X, you will not be able to use the following steps to generate a callstack visualization.  If you wish to generate a callstack visualization, you will need to generate your own data.

**Important**: In the second command below, the file apps/comm\_pattern\_generator/build/comm\_pattern\_generator is an executable file for your project.  Be sure that you run the below commands on KDTS data that was generated from the same executable file as what you input below!

**Note**, also for the second of the following commands, running the script 'callstack_analysis.py', may take a few minutes time to complete:

```
python3 anacin-x/event_graph_analysis/anomaly_detection.py [Path to 'kdts.pkl' file with file name] anacin-x/event_graph_analysis/anomaly_detection_policies/all.json -o flagged_indices.pkl

python3 anacin-x/event_graph_analysis/callstack_analysis.py ['flagged_indices.pkl file name with same path as 'kdts.pkl'] [Path to 'kdts.pkl' file with file name] apps/comm_pattern_generator/build/comm_pattern_generator

python3 anacin-x/event_graph_analysis/visualization/visualize_callstack_report.py ['non_anomaly_report_for_policy_all.txt' file name with same path as 'kdts.pkl'] --plot_type="bar_chart"
```

If the above commands completed with no errors, you will find a file titled 'callstack_distribution.png' within your project directory that will visualize the relative normalized frequencies of callstacks within your communication pattern.  In particular, it will visualize the relative likelihood that each callstack function has an impact on non-determinism in your communication pattern.

If you're doing your work and producing visualizations on a remote machine, remember to copy your png image(s) to your local machine using a tool like scp to view the image.
	
#### Visualizing External Data
	
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

### Reproducing Published Results
	
Visualizations of the above types have been used to produce figures in the publications listed in the publications section below, particularly the paper "Identifying Degrees and Sources of Non-Determinism in MPI Applications via Graph Kernels.".  If the user has access to the applications miniAMR and MCB, such visualizations can be reproduced in the following manners:
	
1. For Figure 17, corresponding to visualizations of the kernel distance time series for MCB, run the kdts visualization script in the visualization section above for external applications. (i.e., use the 'visualize_kernel_distance_time_series.py' script)
2. For Figure 14, corresponding to visualization of callstacks from the miniAMR tool, run the callstack visualization script for external applications. (i.e., use the 'visualize_callstack_report.py' script in the manner outlined above)
3. For Figure 13, corresponding to visualization of kernel distances across different miniAMR time steps, the 'visualize_kernel_distance_time_series.py' script can also be used, but must be accompanied by 'application events' specific to miniAMR.  For miniAMR, these application events correspond to the number of blocks transferred per mesh refinement in a pickle file format.  This is seen in the line showing the '# of Blocks Transferred per Mesh Refinement' in the referenced figure.  The following command shows how to pass these application events into the visualization script.
	
```
python3 visualization/visualize_kernel_distance_time_series.py [Path to 'kdts.pkl' file with file name. This can be found in the directory that stores all your run directories.] --plot_type=box --application_events=blocks_transferred.pkl
```

### Supported Systems:

Currently, the software supports the following types of scheduler systems for job submission.  Make sure that you are running on one of these:
* LSF scheduled systems (ex. Tellico)
* Slurm scheduled systems (ex. Stampede2)
* Unscheduled systems (ex. Jetstream, personal computers)

**Important**: Please refer to the list of command line switches above to determine what settings you can configure.  If your system cannot support the settings requested, then you will need to change them.  The program will not run correctly if you request more processes or nodes than are available in your computer.

Note that if you are trying to generate a callstack visualization, it is strongly recommended to do so on a system that is not running through a virtual machine.  Errors can arise during visualization associated with callstack identification.  
If you are only generating a KDTS visualization, then this is not a limitation.


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
	
Patrick Bell, Kae Suarez, Dylan Chapp, Nigel Tan, Sanjukta Bhowmick, and Michela Taufer. **ANACIN-X: A Software Framework for Studying Non-determinism in MPI Applications.** *Software Impacts, 10:100151*, (2021).

D. Chapp, N. Tan, S. Bhowmick, and M. Taufer. **Identifying Degrees and Sources of Non-Determinism in MPI Applications via Graph Kernels.** *Journal of IEEE Transactions on Parallel and Distributed Systems (IEEE TPDS)*, (2021).

D. Chapp, D. Rorabaugh, K. Sato, D. Ahn, and M. Taufer. **A Three-phase Workflow for General and Expressive Representations of Nondeterminism in HPC Applications.** *International Journal of High-Performance Computing Applications(IJHPCA), 1175-1184* (2019).

D. Chapp, K. Sato, D. Ahn, and M. Taufer. **Record-and-Replay Techniques for HPC Systems: A survey.** *Journal of Supercomputing Frontiers and Innovations, 5(1):11-30.* (2018).

D. Chapp, T. Johnston, and M. Taufer. **On the Need for Reproducible Numerical Accuracy through Intelligent Runtime Selection of Reduction Algorithms at the Extreme Scale.** *In Proceedings of IEEE Cluster Conference, pp. 166 – 175. Chicago, Illinois, USA.* September 8 – 11, 2015.

## Copyright and License:

Copyright (c) 2021, Global Computing Lab

ANACIN-X is distributed under terms of the [Apache License, Version 2.0](http://www.apache.org/licenses/LICENSE-2.0) with LLVM Exceptions.

See [LICENSE](https://github.com/TauferLab/ANACIN-X/blob/master/LICENSE) for more details.



