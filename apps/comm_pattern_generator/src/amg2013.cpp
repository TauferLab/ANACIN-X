#include "amg2013.hpp"

#include <mpi.h>
#include <cstdio>
#include <vector>

void comm_pattern_amg2013( int iter, double nd_fraction, int msg_size )
{
  int mpi_rc, rank, comm_size;
  mpi_rc = MPI_Comm_rank( MPI_COMM_WORLD, &rank );
  mpi_rc = MPI_Comm_size( MPI_COMM_WORLD, &comm_size );
  
  // Determine neighbors
  int n_neighbors = comm_size - 1;
  std::vector<int> neighbors;
  neighbors.reserve( n_neighbors );
  for ( int i=0; i<comm_size; ++i ) {
    if ( i != rank ) {
      neighbors.push_back( i );
    }
  }

  // Determine number of deterministic vs. non-deterministic neighbors
  int n_nd_neighbors = (int) n_neighbors * nd_fraction;
  int n_det_neighbors = n_neighbors - n_nd_neighbors;

  // Set tags for both rounds of communication
  int round_1_tag = 2*iter;
  int round_2_tag = round_1_tag + 1;

  // Post deterministic round-2 receives
  int round_2_recv_buffer_det[ n_det_neighbors ];
  MPI_Request round_2_recv_reqs_det[ n_det_neighbors ];
  for ( int i=0; i<n_det_neighbors; ++i ) {
    auto curr_neighbor = neighbors[ i ];
    mpi_rc = MPI_Irecv( &round_2_recv_buffer_det[i],
                        1, // TODO: swap for msg_size
                        MPI_INT,
                        curr_neighbor,
                        round_2_tag,
                        MPI_COMM_WORLD,
                        &round_2_recv_reqs_det[i] );
  }

  // Post non-deterministic round-2 receives
  int round_2_recv_buffer_nd[ n_nd_neighbors ];
  MPI_Request round_2_recv_reqs_nd[ n_nd_neighbors ];
  for ( int i=0; i<n_nd_neighbors; ++i ) {
    mpi_rc = MPI_Irecv( &round_2_recv_buffer_nd[i],
                        1, // TODO: swap for msg_size
                        MPI_INT,
                        MPI_ANY_SOURCE,
                        round_2_tag,
                        MPI_COMM_WORLD,
                        &round_2_recv_reqs_nd[i] );
  }

  // Post round-1 sends
  int round_1_send_buffer = rank;
  MPI_Request round_1_send_requests[ n_neighbors ];
  for ( int i=0; i<n_neighbors; ++i ) {
    mpi_rc = MPI_Isend( &round_1_send_buffer,
                        1, // TODO: swap for msg_size
                        MPI_INT,
                        neighbors[i],
                        round_1_tag,
                        MPI_COMM_WORLD,
                        &round_1_send_requests[i] );
  }

  // Complete round-1 sends
  mpi_rc = MPI_Waitall( n_neighbors, round_1_send_requests, MPI_STATUSES_IGNORE );

  // Complete requested amount of round-1 sends deterministically 
  // and send replies
  int round_1_recv_buffer_det[ n_det_neighbors ];
  MPI_Status det_recv_status;
  for ( int i=0; i<n_det_neighbors; ++i ) {
    // Receive deterministically
    auto curr_neighbor = neighbors[ i ];
    mpi_rc = MPI_Recv( &round_1_recv_buffer_det[i],
                       1, // TODO: swap for msg_size
                       MPI_INT,
                       curr_neighbor,
                       round_1_tag,
                       MPI_COMM_WORLD,
                       &det_recv_status );
    
    printf("(DETERMINISTIC) Rank: %d round-1 received from rank: %d\n", rank, curr_neighbor);
    
    // Send reply
    int round_2_send_buffer = rank;
    mpi_rc = MPI_Send( &round_2_send_buffer,
                       1, // TODO: swap for msg_size
                       MPI_INT,
                       curr_neighbor,
                       round_2_tag,
                       MPI_COMM_WORLD );
  }

  // Complete remaining amount of round-1 sends non-deterministically
  int round_1_recv_buffer_nd[ n_nd_neighbors ];
  MPI_Status probe_status, nd_recv_status;
  int n_received = 0;
  while ( n_received < n_nd_neighbors ) {
    // Check for a message
    mpi_rc = MPI_Probe( MPI_ANY_SOURCE,
                        round_1_tag,
                        MPI_COMM_WORLD,
                        &probe_status );

    // Get sender from probe status 
    int sender_rank = probe_status.MPI_SOURCE;
    
    // Post matching receive
    mpi_rc = MPI_Recv( &round_1_recv_buffer_nd[ n_received ],
                       1,
                       MPI_INT,
                       sender_rank,
                       round_1_tag,
                       MPI_COMM_WORLD,
                       &nd_recv_status );
    
    printf("(NON-DETERMINISTIC) Rank: %d round-1 received from rank: %d\n", rank, sender_rank);

    // Update number of received messages
    n_received++;

    // Send response
    int round_2_send_buffer = rank;
    mpi_rc = MPI_Send( &round_2_send_buffer,
                       1,
                       MPI_INT,
                       sender_rank,
                       round_2_tag,
                       MPI_COMM_WORLD );
  }

  // Complete deterministic round-1 receives
  MPI_Status round_2_recv_status;
  for ( int i=0; i<n_det_neighbors; ++i ) {
    mpi_rc = MPI_Wait( &round_2_recv_reqs_det[i], &round_2_recv_status );
    printf("(DETERMINISTIC) Rank: %d round-2 received from rank: %d\n", rank, round_2_recv_status.MPI_SOURCE);
  }

  // Complete non-deterministic round-1 receives
  for ( int i=0; i<n_nd_neighbors; ++i ) {
    mpi_rc = MPI_Wait( &round_2_recv_reqs_nd[i], &round_2_recv_status );
    printf("(NON-DETERMINISTIC) Rank: %d round-2 received from rank: %d\n", rank, round_2_recv_status.MPI_SOURCE);
  }

}

//void comm_pattern_amg2013_deterministic( MPI_Comm comm ) 
//{
//  
//  // Determine neighbors
//  std::vector<int> neighbors;
//  neighbors.reserve( comm_size - 1 );
//  for ( int i=0; i<comm_size; ++i ) {
//    if ( i != rank ) {
//      neighbors.push_back( i );
//    }
//  }
//  int n_neighbors = comm_size-1;
//
//  // Define tags for the two rounds of communication
//  int round_1_tag = 0;
//  int round_2_tag = 1;
//
//  // Post round-2 receives 
//  int round_2_recv_buffer[ n_neighbors ];
//  MPI_Request round_2_recv_requests[ n_neighbors ];
//  for ( int i=0; i<n_neighbors; ++i ) {
//    mpi_rc = MPI_Irecv( &round_2_recv_buffer[i],
//                        1,
//                        MPI_INT,
//                        MPI_ANY_SOURCE,
//                        round_2_tag,
//                        comm,
//                        &round_2_recv_requests[i] );
//  }
//
//  // Post round-1 sends
//  int round_1_send_buffer = rank;
//  MPI_Request round_1_send_requests[ n_neighbors ];
//  for ( int i=0; i<n_neighbors; ++i ) {
//    mpi_rc = MPI_Isend( &round_1_send_buffer,
//                        1,
//                        MPI_INT,
//                        neighbors[i],
//                        round_1_tag,
//                        comm,
//                        &round_1_send_requests[i] );
//
//  }
//
//  // Complete round-1 sends
//  mpi_rc = MPI_Waitall( n_neighbors, round_1_send_requests, MPI_STATUSES_IGNORE );
//
//  // Receive round-1 sends
//  int round_1_recv_buffer[ n_neighbors ];
//  MPI_Status probe_status;
//  MPI_Status recv_status;
//  for ( int i=0; i<n_neighbors; ++i ) {
//    
//    // Check for a message
//    mpi_rc = MPI_Probe( neighbors[i],
//                        round_1_tag,
//                        comm,
//                        &probe_status );
//
//    // Get sender from probe status 
//    int sender_rank = probe_status.MPI_SOURCE;
//    
//    // Post matching receive
//    mpi_rc = MPI_Recv( &round_1_recv_buffer[ i ],
//                       1,
//                       MPI_INT,
//                       sender_rank,
//                       round_1_tag,
//                       comm,
//                       &recv_status );
//    
//    printf("(DETERMINISTIC) Rank: %d round-1 received from rank: %d\n", rank, sender_rank);
//
//    // Send response
//    int round_2_send_buffer = round_1_recv_buffer[ i ] + rank;
//    mpi_rc = MPI_Send( &round_2_send_buffer,
//                       1,
//                       MPI_INT,
//                       sender_rank,
//                       round_2_tag,
//                       comm );
//  }
//
//  // Complete round-2 receives
//  MPI_Status round_2_recv_status;
//  for ( int i=0; i<n_neighbors; ++i ) {
//    mpi_rc = MPI_Wait( &round_2_recv_requests[i], &round_2_recv_status );
//    
//    printf("(DETERMINISTIC) Rank: %d round-2 received from rank: %d\n", rank, round_2_recv_status.MPI_SOURCE);
//  }
//}
//
//void comm_pattern_amg2013_non_deterministic( MPI_Comm comm, bool randomize_initial_sends )
//{
//  int mpi_rc, rank, comm_size;
//  mpi_rc = MPI_Comm_rank( comm, &rank );
//  mpi_rc = MPI_Comm_size( comm, &comm_size );
//
//  // Determine neighbors
//  std::vector<int> neighbors;
//  neighbors.reserve( comm_size - 1 );
//  for ( int i=0; i<comm_size; ++i ) {
//    if ( i != rank ) {
//      neighbors.push_back( i );
//    }
//  }
//  int n_neighbors = comm_size-1;
//
//  // Define tags for the two rounds of communication
//  int round_1_tag = 0;
//  int round_2_tag = 1;
//
//  // Post round-2 receives 
//  int round_2_recv_buffer[ n_neighbors ];
//  MPI_Request round_2_recv_requests[ n_neighbors ];
//  for ( int i=0; i<n_neighbors; ++i ) {
//    mpi_rc = MPI_Irecv( &round_2_recv_buffer[i],
//                        1,
//                        MPI_INT,
//                        MPI_ANY_SOURCE,
//                        round_2_tag,
//                        comm,
//                        &round_2_recv_requests[i] );
//  }
//
//  // Post round-1 sends
//  int round_1_send_buffer = rank;
//  MPI_Request round_1_send_requests[ n_neighbors ];
//  for ( int i=0; i<n_neighbors; ++i ) {
//    mpi_rc = MPI_Isend( &round_1_send_buffer,
//                        1,
//                        MPI_INT,
//                        neighbors[i],
//                        round_1_tag,
//                        comm,
//                        &round_1_send_requests[i] );
//
//  }
//
//  // Complete round-1 sends
//  mpi_rc = MPI_Waitall( n_neighbors, round_1_send_requests, MPI_STATUSES_IGNORE );
//
//  // Receive round-1 sends
//  int n_expected = n_neighbors;
//  int n_received = 0;
//  int round_1_recv_buffer[ n_neighbors ];
//  MPI_Status probe_status;
//  MPI_Status recv_status;
//  while ( n_received < n_expected ) {
//    
//    // Check for a message
//    mpi_rc = MPI_Probe( MPI_ANY_SOURCE,
//                        round_1_tag,
//                        comm,
//                        &probe_status );
//
//    // Get sender from probe status 
//    int sender_rank = probe_status.MPI_SOURCE;
//    
//    // Post matching receive
//    mpi_rc = MPI_Recv( &round_1_recv_buffer[ n_received ],
//                       1,
//                       MPI_INT,
//                       sender_rank,
//                       round_1_tag,
//                       comm,
//                       &recv_status );
//    
//    printf("(NON-DETERMINISTIC) Rank: %d round-1 received from rank: %d\n", rank, sender_rank);
//
//    // Update number of received messages
//    n_received++;
//
//    // Send response
//    int round_2_send_buffer = round_1_recv_buffer[ n_received-1 ] + rank;
//    mpi_rc = MPI_Send( &round_2_send_buffer,
//                       1,
//                       MPI_INT,
//                       sender_rank,
//                       round_2_tag,
//                       comm );
//  }
//
//  // Complete round-2 receives
//  MPI_Status round_2_recv_statuses[ n_neighbors ];
//  mpi_rc = MPI_Waitall( n_neighbors, round_2_recv_requests, round_2_recv_statuses );
//
//  for ( int i=0; i<n_neighbors; ++i ) {
//    printf("(NON-DETERMINISTIC) Rank: %d round-2 received from rank: %d\n", rank, round_2_recv_statuses[i].MPI_SOURCE);
//  }
//}
