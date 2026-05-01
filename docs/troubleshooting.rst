Troubleshooting
===============

Run ``./setup_deps.sh --check`` whenever installation fails. It verifies the
most common issues without changing the environment.

Common Installation Issues
--------------------------

``spack`` was not found
   Source Spack first with ``. /path/to/spack/share/spack/setup-env.sh``.

``conda`` was not found
   Initialize Miniconda or Anaconda in the current shell, then reopen the shell
   or source the updated startup file.

No active Conda environment
   Run ``conda create -n anacin-x python=3.8 -y`` once, then
   ``conda activate anacin-x``.

Conda asks for Terms of Service acceptance
   Either re-run ``./install_all.sh --accept-conda-tos`` if you agree to those
   terms, or run the ``conda tos accept --override-channels --channel ...``
   commands shown by Conda manually.

Wrong Python version
   ANACIN-X currently expects Python 3.8 for its Python dependencies.

``mpicc`` was not found
   Load your MPI module or install/load MPI with Spack, for example
   ``spack install openmpi && spack load openmpi``. Match the loaded MPI
   implementation with the ``--mpi`` option passed to ``setup_deps.sh``.

Spack reports deprecated package versions
   This is expected for some ANACIN-X dependencies. The installer uses Spack's
   ``--deprecated`` flag automatically.

A partial install failed
   Fix the reported issue, re-run ``./setup_deps.sh --check``, then re-run
   ``. ./setup_deps.sh --mpi <name>``. Re-running the dependency installer
   refreshes the Spack environment manifest.

Submodule rebuild safety
   ``setup.sh`` currently cleans the ``submodules/`` directory before fetching
   and rebuilding dependencies. Do not run it while you have local submodule
   edits you need to preserve.
