#ifndef NAIVE_REDUCE_H
#define NAIVE_REDUCE_H

#include <mpi.h>

void comm_pattern_naive_reduce( int iter, double nd_fraction, int msg_size, bool interleave_nd_recvs, bool compute=false, double min=0.0, double max=1.0, int seed=0 );

//void comm_pattern_naive_reduce_non_deterministic( MPI_Comm comm );
//void comm_pattern_naive_reduce_deterministic( MPI_Comm comm );

#endif
