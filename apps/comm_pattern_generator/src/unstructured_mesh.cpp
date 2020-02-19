#include "unstructured_mesh.hpp"

#include <mpi.h>
#include <cstdio>
#include <cstdlib>
#include <cmath>
#include <ctime>
#include <vector>
#include <unordered_set>
#include <iostream>

#include "debug.hpp"

int coords_to_rank( int x_coord, int y_coord, int z_coord, int n_procs_x, int n_procs_y )
{
  return ( x_coord 
           + ( y_coord * n_procs_x )
           + ( z_coord * n_procs_x * n_procs_y ) );
}

int rand_translate( int coord, int max_coord, int max_dist )
{   
  auto direction = ( ( std::rand() % 2 ) ? -1 : 1 );
  auto distance = std::rand() % max_dist;
  auto new_coord = ( coord + ( direction * distance ) ) % max_coord;
  if ( new_coord < 0 ) {
    new_coord = max_coord + new_coord;
  }
  return new_coord;
}

int rank_to_dist( int src_rank, int dst_rank, int n_procs_x, int n_procs_y, int n_procs_z )
{
  // Compute source rank coordinates
  int src_x_coord = src_rank % n_procs_x;
  int src_y_coord = ( src_rank % ( n_procs_x * n_procs_y ) ) / n_procs_x;
  int src_z_coord = ( src_rank % ( n_procs_x * n_procs_y * n_procs_z ) ) / ( n_procs_x * n_procs_y );
  
  // Compute destination rank coordinates
  int dst_x_coord = dst_rank % n_procs_x;
  int dst_y_coord = ( dst_rank % ( n_procs_x * n_procs_y ) ) / n_procs_x;
  int dst_z_coord = ( dst_rank % ( n_procs_x * n_procs_y * n_procs_z ) ) / ( n_procs_x * n_procs_y );

  // Compute manhattan distance 
  int dist = ( std::abs( dst_x_coord - src_x_coord ) +
               std::abs( dst_y_coord - src_y_coord ) + 
               std::abs( dst_z_coord - src_z_coord ) );
  return dist;
}

void comm_pattern_unstructured_mesh( int iter, double nd_fraction, 
                                     int n_procs_x, int n_procs_y, int n_procs_z, 
                                     int min_deg, int max_deg, int max_dist, int msg_size )
{
  int mpi_rc, rank, comm_size;
  mpi_rc = MPI_Comm_rank( MPI_COMM_WORLD, &rank );
  mpi_rc = MPI_Comm_size( MPI_COMM_WORLD, &comm_size );

  // Determine my coordinates
  int x_coord = rank % n_procs_x;
  int y_coord = ( rank % ( n_procs_x * n_procs_y ) ) / n_procs_x;
  int z_coord = ( rank % ( n_procs_x * n_procs_y * n_procs_z ) ) / ( n_procs_x * n_procs_y );

  // Determine whether this process should pick its neighbors deterministically
  // or non-deterministically. 
  // If deterministic, RNG is seeded same way each iteration
  // If not, RNG is seeded differently on each iteration
  auto max_nd_rank = (int) (comm_size) * nd_fraction;
  if ( rank < max_nd_rank ) {
    std::srand( std::time(NULL) + iter );
  } else {
    std::srand( rank );
  }

  // Determine number of destinations
  int range = max_deg - min_deg;
  // Guarantee range of at least one
  (range > 0) ? range : 1;
  int degree = min_deg + ( std::rand() % range );

  // Determine who this process's destinations are
  std::unordered_set<int> destination_set;
  std::vector<int> destinations;
  for (int i=0; i<degree; ++i ) {
    int dst_rank = rank;
    // Randomize next destination until it isn't own rank
    while (true) {
      int dst_x_coord = rand_translate( x_coord, n_procs_x, max_dist );
      int dst_y_coord = rand_translate( y_coord, n_procs_y, max_dist );
      int dst_z_coord = rand_translate( z_coord, n_procs_z, max_dist );
      dst_rank = coords_to_rank( dst_x_coord, dst_y_coord, dst_z_coord, 
                                 n_procs_x, n_procs_y );
#ifdef DEBUG 
      std::cout << "My Rank: " << rank 
                << " My Position: (" << x_coord << ", " << y_coord << ", " << z_coord << ")" 
                << " Neighbor Position: (" << dst_x_coord << ", " << dst_y_coord << ", " << dst_z_coord << ")" 
                << " Neighbor Rank: " << dst_rank
                << std::endl;
#endif

      // Only accept a destination if it is:
      // 1. Not self rank
      // 2. Not already a destination
      if ( dst_rank != rank and destination_set.find(dst_rank) == destination_set.end() ) {
        destination_set.insert( dst_rank );
        break;
      }
    }
    destinations.push_back( dst_rank );
  }
 
#ifdef DEBUG
  std::cout << "Rank: " << rank << ", # destinations = " << degree << ", destinations: ";
  for ( auto n : destinations ) {
    std::cout << n << " ";
  }
  std::cout << std::endl;
#endif

  // Determine how many messages this process will receive
  int* local_counts = new int[comm_size];
  for ( int i=0; i<comm_size; ++i ) {
    local_counts[i] = 0;
  }
  for ( int i=0; i<degree; ++i ) {
    local_counts[ destinations[i] ]++;
  }
  int* global_counts = new int[comm_size];
  mpi_rc = MPI_Allreduce( local_counts, 
                          global_counts, 
                          comm_size, 
                          MPI_INTEGER, 
                          MPI_SUM, 
                          MPI_COMM_WORLD );
  int n_neighbors = global_counts[ rank ];
  delete [] local_counts;
  delete [] global_counts;

  // Allocate send and receive buffers 
  char* send_buffer = (char*) malloc (degree * msg_size * sizeof(char));
  char* recv_buffer = (char*) malloc (n_neighbors * msg_size * sizeof(char));

  // Allocate requests
  MPI_Request * send_reqs = new MPI_Request[ degree ];
  MPI_Request * recv_reqs = new MPI_Request[ n_neighbors ];
  
  // Post communication requests
  for (int j = 0; j < n_neighbors; j++) {
    MPI_Irecv( &recv_buffer[j * msg_size], 
               msg_size, 
               MPI_CHAR, 
               MPI_ANY_SOURCE, 
               iter,
               MPI_COMM_WORLD, 
               &recv_reqs[j] );
  }
  for (int j = 0; j < degree; j++) {
    MPI_Isend( &send_buffer[j * msg_size], 
               msg_size, 
               MPI_CHAR, 
               destinations[j], 
               iter,
               MPI_COMM_WORLD, 
               &send_reqs[j] );
  } 
  
  // Complete communication requests
  MPI_Waitall(degree, &send_reqs[0], MPI_STATUSES_IGNORE);
  MPI_Status recv_statuses[ n_neighbors ];
  MPI_Waitall(n_neighbors, &recv_reqs[0], &recv_statuses[0]);
}

