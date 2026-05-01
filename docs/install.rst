Installation
============

ANACIN-X is easiest to install on Linux with Spack, Conda, an MPI compiler
wrapper, and Python 3.8. The dependency installer is non-interactive by default
and provides a preflight check before it starts the long build.

Fresh Linux Installation
------------------------

Use these steps on a fresh Linux machine. They assume Bash, network access, and
a working system C/C++ compiler. On a cluster, load the site-provided
compiler/MPI modules instead of installing MPI with Spack.

1. Install and activate Spack.

.. code-block:: bash

   git clone --depth=2 https://github.com/spack/spack.git $HOME/spack
   . $HOME/spack/share/spack/setup-env.sh
   spack compiler find

To make Spack available automatically in future Bash shells:

.. code-block:: bash

   grep -qxF '. $HOME/spack/share/spack/setup-env.sh' ~/.bashrc || echo '. $HOME/spack/share/spack/setup-env.sh' >> ~/.bashrc

2. Install Miniconda.

.. code-block:: bash

   mkdir -p $HOME/miniconda3
   curl -O https://repo.anaconda.com/miniconda/Miniconda3-latest-Linux-x86_64.sh
   bash ./Miniconda3-latest-Linux-x86_64.sh

Open a new shell, or source your shell startup file, before continuing.

3. Create and activate the ANACIN-X Conda environment.

.. code-block:: bash

   . $HOME/spack/share/spack/setup-env.sh
   conda create -n anacin-x python=3.8 -y
   conda activate anacin-x

4. Install or load MPI.

.. code-block:: bash

   spack install openmpi
   spack load openmpi
   mpicc --version

If your system already provides MPI, load that MPI instead and pass the matching
``--mpi`` value to ``setup_deps.sh``: ``openmpi``, ``mpich``, or ``mvapich2``.

5. Clone ANACIN-X and install its dependencies.

.. code-block:: bash

   git clone https://github.com/TauferLab/ANACIN-X.git
   cd ANACIN-X
   ./setup_deps.sh --check
   . ./setup_deps.sh --mpi openmpi

6. Build ANACIN-X.

.. code-block:: bash

   . ./setup.sh -c

The ``-c`` option enables callstack tracing through CSMPI. To build without
callstack tracing, run ``. ./setup.sh``.

Source the full dependency install command with ``. ./setup_deps.sh`` so Spack
package loads remain available in the current shell before running
``setup.sh``. The ``--check`` mode can be run normally because it does not
install or load packages. Use ``--spack-env <name>`` if you want a Spack
environment name other than ``anacin_spack_env``.

Existing Environment Installation
---------------------------------

Use this shorter path if ``spack``, ``conda``, and ``mpicc`` are already
available in your shell.

.. code-block:: bash

   . /path/to/spack/share/spack/setup-env.sh
   conda activate anacin-x
   spack load openmpi

   git clone https://github.com/TauferLab/ANACIN-X.git
   cd ANACIN-X
   ./setup_deps.sh --check
   . ./setup_deps.sh --mpi openmpi
   . ./setup.sh -c

Use ``--mpi mpich`` or ``--mpi mvapich2`` if that is the MPI implementation
loaded on your system.

Build Behavior
--------------

``setup.sh`` fetches and builds ANACIN-X submodules, patches tracing libraries
for PnMPI, builds the communication-pattern generator, and writes local machine
settings to ``anacin-x/config/anacin_paths.local.config``. It also cleans the
``submodules/`` directory before fetching; do not run it while you have local
submodule edits you need to keep.

Ready-to-use Options
--------------------

If you want to avoid a local dependency build, use one of the ready-to-use
environments:

* Open the reproducible capsule from the **Open in Code Ocean** badge in the
  project README.
* Use the Jetstream image named ``Ubuntu20.04_Anacin-X``; it already has the
  expected ANACIN-X environment.
* Use the Apptainer/Singularity-ready container linked in the project README's
  Reproducibility section.
