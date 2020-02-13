#ifndef NAIVE_REDUCE_H
#define NAIVE_REDUCE_H

#include <mpi.h>

void comm_pattern_naive_reduce( MPI_Comm comm, bool deterministic );
void comm_pattern_naive_reduce_non_deterministic( MPI_Comm comm );
void comm_pattern_naive_reduce_deterministic( MPI_Comm comm );

#endif
