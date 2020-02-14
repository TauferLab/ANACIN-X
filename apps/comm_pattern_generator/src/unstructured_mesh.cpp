#include "unstructured_mesh.hpp"

#include <mpi.h>
#include <cstdio>
#include <cstdlib>
#include <cmath>
#include <vector>


int coords_to_rank( int x_coord, int y_coord, int z_coord, int n_procs_x, int n_procs_y )
{
  return ( x_coord 
           + ( y_coord * n_procs_x )
           + ( z_coord * n_procs_x * n_procs_y ) );
}

int wrap( int x, int n_procs )
{
  return ( x + n_procs ) % n_procs;
}

void comm_pattern_unstructured_mesh( MPI_Comm comm, bool deterministic )
{
  if ( deterministic ) {
    comm_pattern_unstructured_mesh_deterministic( comm );
  } else {
    comm_pattern_unstructured_mesh_non_deterministic( comm );
  }
}

void comm_pattern_unstructured_mesh_deterministic( MPI_Comm comm ) 
{
  int mpi_rc, rank, comm_size;
  mpi_rc = MPI_Comm_rank( comm, &rank );
  mpi_rc = MPI_Comm_size( comm, &comm_size );
}

void comm_pattern_unstructured_mesh_non_deterministic( MPI_Comm comm )
{
  int mpi_rc, rank, comm_size;
  mpi_rc = MPI_Comm_rank( comm, &rank );
  mpi_rc = MPI_Comm_size( comm, &comm_size );

}
