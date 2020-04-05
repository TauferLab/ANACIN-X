#include "naive_reduce.hpp"

#include <mpi.h>
#include <cstdio>
#include <cmath>
#include <cstring>
#include <iostream>
#include <random>
#include <limits>

#include "debug.hpp"

void comm_pattern_naive_reduce( int iter, double nd_fraction, int msg_size, 
                                bool interleave_nd_recvs, bool compute, 
                                double min, double max, int seed )
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

  if( compute ) {
    // Deterministic reduction for reference
    if(seed == 0)
      seed += rank;
    std::default_random_engine generator(seed);
    std::uniform_real_distribution<double> unif_rand(min, max);
    double* local_vals = (double*) malloc(sizeof(double)*msg_size);
    for(int i=0; i<msg_size; i++) {
      local_vals[i] = unif_rand(generator);
    }
    double det_global_val = 0.0;
    double ndet_global_val = 0.0;
    if(rank == 0) {
      MPI_Status status;
      for(int i=0; i<comm_size-1; i++) {
        mpi_rc = MPI_Recv(local_vals, msg_size, MPI_DOUBLE, i+1, iter, MPI_COMM_WORLD, &status);
        for(int j=0; j<msg_size; j++) {
          det_global_val += local_vals[j];
        }
      }
    }
    else
    {
      mpi_rc = MPI_Send(local_vals, msg_size, MPI_DOUBLE, 0, iter, MPI_COMM_WORLD);
    }

    // Non deterministic reduction
    if(rank == 0) {
      MPI_Status status;
      for(int i=0; i<n_det_recvs; i++) {
        mpi_rc = MPI_Recv(local_vals, msg_size, MPI_DOUBLE, i+1, iter, MPI_COMM_WORLD, &status);
        for(int j=0; j<msg_size; j++) {
          ndet_global_val += local_vals[j];
        }
      }
      for(int i=0; i<n_nd_recvs; i++) {
        mpi_rc = MPI_Recv(local_vals, msg_size, MPI_DOUBLE, MPI_ANY_SOURCE, iter, MPI_COMM_WORLD, &status);
        for(int j=0; j<msg_size; j++) {
          ndet_global_val += local_vals[j];
        }
      }
    }
    else
    {
      mpi_rc = MPI_Send(local_vals, msg_size, MPI_DOUBLE, 0, iter, MPI_COMM_WORLD);
    }
    if(rank == 0) {
      std::cout.precision(std::numeric_limits<double>::max_digits10);
      std::cout << "Iteration: " << iter << " Serial deterministic sum: " << det_global_val << " Non-det sum: " << ndet_global_val << std::endl;
    }
    free(local_vals);
  } else {
    // Check whether we are allowing ND receives to interleave with 
    // deterministic receives or not
    if ( !interleave_nd_recvs ) {
      // Root posts receives
      if ( rank == 0 ) {
        char* recv_buffer = (char*) malloc( msg_size * sizeof(char) );
        MPI_Status status;
        // Post receives for deterministically ordered messages
        for (int i=0; i<n_det_recvs; ++i ) {
          mpi_rc = MPI_Recv( recv_buffer, 
                             msg_size,
                             MPI_CHAR,
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
                             MPI_CHAR,
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
        char* send_buffer = (char*) malloc( msg_size * sizeof(char) );
        std::memset( send_buffer, rank, sizeof(send_buffer) );
        mpi_rc = MPI_Send( send_buffer,
                           msg_size,
                           MPI_CHAR,
                           0,
                           iter,
                           MPI_COMM_WORLD );
        // Free send buffer
        free( send_buffer );
      }
    } 
  }
  
//  // Check whether we are allowing ND receives to interleave with 
//  // deterministic receives or not
//  if ( !interleave_nd_recvs ) {
//    // Root posts receives
//    if ( rank == 0 ) {
//      char* recv_buffer = (char*) malloc( msg_size * sizeof(char) );
//      MPI_Status status;
//      // Post receives for deterministically ordered messages
//      for (int i=0; i<n_det_recvs; ++i ) {
//        mpi_rc = MPI_Recv( recv_buffer, 
//                           msg_size,
//                           MPI_CHAR,
//                           i+1,
//                           iter,
//                           MPI_COMM_WORLD,
//                           &status );
//#ifdef DEBUG
//        std::cout << "(DET) Received from rank: " << i+1 << std::endl;
//#endif
//      }
//      // Post receives for non-deterministically ordered messages
//      for (int i=0; i<n_nd_recvs; ++i ) {
//        mpi_rc = MPI_Recv( recv_buffer, 
//                           msg_size,
//                           MPI_CHAR,
//                           MPI_ANY_SOURCE,
//                           iter,
//                           MPI_COMM_WORLD,
//                           &status );
//#ifdef DEBUG
//        std::cout << "(ND) Received from rank: " << status.MPI_SOURCE << std::endl;
//#endif
//      }
//      // Free receive buffer
//      free( recv_buffer );
//    }
//    // Others send single message
//    else {
//      char* send_buffer = (char*) malloc( msg_size * sizeof(char) );
//      std::memset( send_buffer, rank, sizeof(send_buffer) );
//      mpi_rc = MPI_Send( send_buffer,
//                         msg_size,
//                         MPI_CHAR,
//                         0,
//                         iter,
//                         MPI_COMM_WORLD );
//      // Free send buffer
//      free( send_buffer );
//    }
//  } 
}

