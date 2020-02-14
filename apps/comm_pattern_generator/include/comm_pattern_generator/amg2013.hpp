#ifndef AMG2013_H
#define AMG2013_H

#include <mpi.h>

void comm_pattern_amg2013( MPI_Comm comm, bool deterministic, bool randomize_initial_sends );
void comm_pattern_amg2013_non_deterministic( MPI_Comm comm, bool randomize_initial_sends );
void comm_pattern_amg2013_deterministic( MPI_Comm comm );

#endif
