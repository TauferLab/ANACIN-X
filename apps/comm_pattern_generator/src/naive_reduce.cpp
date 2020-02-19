#include "naive_reduce.hpp"

#include <mpi.h>
#include <cstdio>
#include <cmath>
#include <cstring>
#include <iostream>

#include "debug.hpp"

void comm_pattern_naive_reduce( int iter, double nd_fraction, int msg_size, bool interleave_nd_recvs  )
{
  int mpi_rc, rank, comm_size;
  mpi_rc = MPI_Comm_rank( MPI_COMM_WORLD, &rank );
  mpi_rc = MPI_Comm_size( MPI_COMM_WORLD, &comm_size );
  // Determine number of ND receives
  int n_nd_recvs = (int) (comm_size-1) * nd_fraction;
  int n_det_recvs = comm_size - ( n_nd_recvs + 1 );

#ifdef DEBUG
  if ( rank == 0 ) {
    std::cout << "Iteration: " << iter
              << " # non-deterministic recvs: " << n_nd_recvs 
              << " # deterministic recvs: " << n_det_recvs 
              << std::endl;
  }
#endif

  // Check whether we are allowing ND receives to interleave with 
  // deterministic receives or not
  if ( !interleave_nd_recvs ) {
    // Root posts receives
    if ( rank == 0 ) {
      int* recv_buffer = (int*) malloc( msg_size * sizeof(int) );
      MPI_Status status;
      // Post receives for deterministically ordered messages
      for (int i=0; i<n_det_recvs; ++i ) {
        mpi_rc = MPI_Recv( recv_buffer, 
                           msg_size,
                           MPI_INT,
                           i+1,
                           iter,
                           MPI_COMM_WORLD,
                           &status );
#ifdef DEBUG
        std::cout << "(DET) Received from rank: " << i+1 << std::endl;
#endif
      }
      // Post receives for non-deterministically ordered messages
      for (int i=0; i<n_nd_recvs; ++i ) {
        mpi_rc = MPI_Recv( recv_buffer, 
                           msg_size,
                           MPI_INT,
                           MPI_ANY_SOURCE,
                           iter,
                           MPI_COMM_WORLD,
                           &status );
#ifdef DEBUG
        std::cout << "(ND) Received from rank: " << status.MPI_SOURCE << std::endl;
#endif
      }
      // Free receive buffer
      free( recv_buffer );
    }
    // Others send single message
    else {
      int* send_buffer = (int*) malloc( msg_size * sizeof(int) );
      std::memset( send_buffer, rank, sizeof(send_buffer) );
      mpi_rc = MPI_Send( send_buffer,
                         msg_size,
                         MPI_INT,
                         0,
                         iter,
                         MPI_COMM_WORLD );
      // Free send buffer
      free( send_buffer );
    }
  } 
}

