#include <mpi.h>
#include <cstdio>
#include <cstdlib>

#include "naive_reduce.hpp"
#include "amg2013.hpp"

int main( int argc, char** argv )
{
  int mpi_rc, rank, comm_size;
  mpi_rc = MPI_Init( nullptr, nullptr );
  mpi_rc = MPI_Comm_rank( MPI_COMM_WORLD, &rank );
  mpi_rc = MPI_Comm_size( MPI_COMM_WORLD, &comm_size );

  int color;
  if ( rank < 4 ) {
    color = 0;
  } else {
    color = 1;
  }

  MPI_Comm pattern_comm;
  mpi_rc = MPI_Comm_split( MPI_COMM_WORLD, color, rank, &pattern_comm);

  int pattern_comm_rank, pattern_comm_size;
  mpi_rc = MPI_Comm_rank( pattern_comm, &pattern_comm_rank );
  mpi_rc = MPI_Comm_size( pattern_comm, &pattern_comm_size );

  comm_pattern_naive_reduce( pattern_comm, color );

  mpi_rc = MPI_Comm_free( &pattern_comm );

  mpi_rc = MPI_Finalize();
  return EXIT_SUCCESS;
}
