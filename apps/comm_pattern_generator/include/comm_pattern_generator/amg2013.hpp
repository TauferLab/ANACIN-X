#ifndef AMG2013_H
#define AMG2013_H

#include <mpi.h>

void comm_pattern_amg2013( int iter, double nd_fraction, int msg_size, bool compute=false, double min=0.0, double max=1.0, int seed=0 );

#endif
