#include <mpi.h>
#include <cstdio>
#include <cstdlib>

void comm_pattern_naive_reduce_non_deterministic( MPI_Comm comm );
void comm_pattern_naive_reduce_deterministic( MPI_Comm comm );

void comm_pattern_naive_reduce( MPI_Comm comm, bool deterministic, int global_rank )
{
  if ( deterministic ) {
    comm_pattern_naive_reduce_deterministic( comm );
  } else {
    comm_pattern_naive_reduce_non_deterministic( comm );
  }
}

void comm_pattern_naive_reduce_deterministic( MPI_Comm comm ) 
{
  int mpi_rc, rank, comm_size;
  mpi_rc = MPI_Comm_rank( comm, &rank );
  mpi_rc = MPI_Comm_size( comm, &comm_size );
  // Root receives in rank-order from senders
  if ( rank == 0 ) {
    int recv_buffer; 
    MPI_Status status;
    for ( int i=1; i<comm_size; ++i ) {
      mpi_rc = MPI_Recv( &recv_buffer,
                         1,
                         MPI_INT,
                         i,
                         0,
                         comm,
                         &status );
      printf( "Deterministic Pattern: received from rank: %d\n", i );
    }
  } 
  // Others send single message to root
  else {
    int send_buffer = rank;
    mpi_rc = MPI_Send( &send_buffer,
                       1,
                       MPI_INT,
                       0,
                       0,
                       comm );
  }
}

void comm_pattern_naive_reduce_non_deterministic( MPI_Comm comm )
{
  int mpi_rc, rank, comm_size;
  mpi_rc = MPI_Comm_rank( comm, &rank );
  mpi_rc = MPI_Comm_size( comm, &comm_size );
  // Root receives in arbitrary order from senders
  if ( rank == 0 ) {
    int recv_buffer; 
    int n_messages_expected = comm_size-1;
    MPI_Request requests[ n_messages_expected ];
    // Post a receive for each sender
    for ( int i=1; i<comm_size; ++i ) {
      mpi_rc = MPI_Irecv( &recv_buffer,
                         1,
                         MPI_INT,
                         i,
                         0,
                         comm,
                         &requests[i-1] );
    }
    int n_messages_received = 0;
    MPI_Status status;
    int request_idx;
    while ( n_messages_received < n_messages_expected ) {
      mpi_rc = MPI_Waitany( n_messages_expected, requests, &request_idx, &status );
      printf( "ND Pattern: received from rank: %d\n", status.MPI_SOURCE );
      n_messages_received++;
    }
  } 
  // Others send single message to root
  else {
    int send_buffer = rank;
    mpi_rc = MPI_Send( &send_buffer,
                       1,
                       MPI_INT,
                       0,
                       0,
                       comm );
  }
}

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
  MPI_Comm_split( MPI_COMM_WORLD, color, rank, &pattern_comm);

  int pattern_comm_rank, pattern_comm_size;
  mpi_rc = MPI_Comm_rank( pattern_comm, &pattern_comm_rank );
  mpi_rc = MPI_Comm_size( pattern_comm, &pattern_comm_size );

  //printf("Global Rank: %d, Pattern Comm Rank: %d\n", rank, pattern_comm_rank);
 
  comm_pattern_naive_reduce( pattern_comm, color, rank );

  mpi_rc = MPI_Comm_free( &pattern_comm );

  mpi_rc = MPI_Finalize();
  return EXIT_SUCCESS;
}
