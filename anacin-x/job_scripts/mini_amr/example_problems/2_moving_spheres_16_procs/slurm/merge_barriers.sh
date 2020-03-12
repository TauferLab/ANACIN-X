#!/usr/bin/env bash

#SBATCH -o merge_barriers-%j.out
#SBATCH -e merge_barriers-%j.err

merge_barriers_script=$1
event_graph=$2

srun -N1 -n1 ${merge_barriers_script} ${event_graph}
