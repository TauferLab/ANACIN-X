#ifndef MCB_GRID_H
#define MCB_GRID_H

#include <mpi.h>

void comm_pattern_mcb_grid( int iter, double nd_fraction_send, double nd_fraction_recv,
                            int n_neighbors, int n_steps, int msg_size );
void shuffle( int* array, int size );
int get_neighbor( int my_rank, int comm_size, int neighbor_idx );

#endif 
