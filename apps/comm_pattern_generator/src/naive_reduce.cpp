#include "naive_reduce.hpp"

#include <mpi.h>
#include <cstdio>
#include <cmath>
#include <cstring>
#include <iostream>

void comm_pattern_naive_reduce( int iter, double nd_fraction, int msg_size, bool interleave_nd_recvs  )
{
  int mpi_rc, rank, comm_size;
  mpi_rc = MPI_Comm_rank( MPI_COMM_WORLD, &rank );
  mpi_rc = MPI_Comm_size( MPI_COMM_WORLD, &comm_size );
  // Determine number of ND receives
  int n_nd_recvs = (int) (comm_size-1) * nd_fraction;
  int n_det_recvs = comm_size - ( n_nd_recvs + 1 );

  if ( rank == 0 ) {
    std::cout << "Iteration: " << iter
              << " # non-deterministic recvs: " << n_nd_recvs 
              << " # deterministic recvs: " << n_det_recvs 
              << std::endl;
  }

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
        std::cout << "(DET) Received from rank: " << i+1 << std::endl;
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
        std::cout << "(ND) Received from rank: " << status.MPI_SOURCE << std::endl;
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

//void comm_pattern_naive_reduce_deterministic( MPI_Comm comm ) 
//{
//  int mpi_rc, rank, comm_size;
//  mpi_rc = MPI_Comm_rank( comm, &rank );
//  mpi_rc = MPI_Comm_size( comm, &comm_size );
//  // Root receives in rank-order from senders
//  if ( rank == 0 ) {
//    int recv_buffer; 
//    MPI_Status status;
//    for ( int i=1; i<comm_size; ++i ) {
//      mpi_rc = MPI_Recv( &recv_buffer,
//                         1,
//                         MPI_INT,
//                         i,
//                         0,
//                         comm,
//                         &status );
//      printf( "Deterministic Pattern: received from rank: %d\n", i );
//    }
//  } 
//  // Others send single message to root
//  else {
//    int send_buffer = rank;
//    mpi_rc = MPI_Send( &send_buffer,
//                       1,
//                       MPI_INT,
//                       0,
//                       0,
//                       comm );
//  }
//}
//
//void comm_pattern_naive_reduce_non_deterministic( MPI_Comm comm )
//{
//  int mpi_rc, rank, comm_size;
//  mpi_rc = MPI_Comm_rank( comm, &rank );
//  mpi_rc = MPI_Comm_size( comm, &comm_size );
//  // Root receives in arbitrary order from senders
//  if ( rank == 0 ) {
//    int recv_buffer; 
//    int n_messages_expected = comm_size-1;
//    MPI_Request requests[ n_messages_expected ];
//    // Post a receive for each sender
//    for ( int i=1; i<comm_size; ++i ) {
//      mpi_rc = MPI_Irecv( &recv_buffer,
//                         1,
//                         MPI_INT,
//                         i,
//                         0,
//                         comm,
//                         &requests[i-1] );
//    }
//    int n_messages_received = 0;
//    MPI_Status status;
//    int request_idx;
//    while ( n_messages_received < n_messages_expected ) {
//      mpi_rc = MPI_Waitany( n_messages_expected, requests, &request_idx, &status );
//      printf( "ND Pattern: received from rank: %d\n", status.MPI_SOURCE );
//      n_messages_received++;
//    }
//  } 
//  // Others send single message to root
//  else {
//    int send_buffer = rank;
//    mpi_rc = MPI_Send( &send_buffer,
//                       1,
//                       MPI_INT,
//                       0,
//                       0,
//                       comm );
//  }
//}
