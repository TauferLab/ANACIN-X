#include "mcb_grid.hpp"

#include <mpi.h>
#include <cstdlib>
#include <ctime>

void shuffle(int* array, int size) {
  if(size > 1) {
    int i;
    for(i=0; i<size-1; i++) {
      int j = i + std::rand() / (RAND_MAX / (size - i) + 1);
      int t = array[j];
      array[j] = array[i];
      array[i] = t;
    }
  }
}

int get_neighbor( int my_rank, int comm_size, int neighbor_idx )
{
  return ( my_rank + ( neighbor_idx + 1 ) ) % comm_size;   
}

void comm_pattern_mcb_grid( int iter, double nd_fraction_send, double nd_fraction_recv,
                            int n_neighbors, int n_steps, int msg_size,
                            bool compute, double min, double max, int seed )
{
  int mpi_rc, rank, comm_size;
  mpi_rc = MPI_Comm_rank( MPI_COMM_WORLD, &rank );
  mpi_rc = MPI_Comm_size( MPI_COMM_WORLD, &comm_size );
}
