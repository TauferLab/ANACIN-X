#include "unstructured_mesh.hpp"

#include <mpi.h>
#include <cstdio>
#include <cstdlib>
#include <cmath>
#include <ctime>
#include <vector>
#include <unordered_set>
#include <iostream>
#include <random>
#include <limits>

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

void comm_pattern_unstructured_mesh( int iter, double nd_fraction_neighbors, double nd_fraction_recvs,
                                     int n_procs_x, int n_procs_y, int n_procs_z, 
                                     int min_deg, int max_deg, int max_dist, int msg_size,
                                     bool compute, double min, double max, int seed )
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
  auto max_nd_rank = (int) (comm_size) * nd_fraction_neighbors;
  if ( rank < max_nd_rank ) {
    std::srand( std::time(NULL) + iter );
  } else {
    std::srand( rank );
  }

  // Determine number of destinations
  int degree = (std::rand() % (max_deg + 1 - min_deg)) + min_deg;

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
  mpi_rc = MPI_Barrier(MPI_COMM_WORLD);
#endif
  

  // Determine who will be received from
  std::vector<int> senders;
  for ( int curr_rank=0; curr_rank<comm_size; ++curr_rank ) {
    // First the current process broadcasts how many others it plans to send to
    int n_destinations;
    if ( rank == curr_rank ) {
      n_destinations = destinations.size();
    }
    mpi_rc = MPI_Bcast( &n_destinations, 1, MPI_INT, curr_rank, MPI_COMM_WORLD );
    // Next it broadcasts which others it plans to send to
    int buffer[ n_destinations ];
    if ( rank == curr_rank ) {
      for ( int i=0; i<destinations.size(); ++i ) {
        buffer[i] = destinations[i];
      }
    }
    mpi_rc = MPI_Bcast( &buffer[0], n_destinations, MPI_INT, curr_rank, MPI_COMM_WORLD );
    // Next all other processes check to see if they are an upcoming 
    // destination of the current process
    if ( rank != curr_rank ) {
      for ( int i=0; i<n_destinations; ++i ) {
        if ( buffer[i] == rank ) {
          senders.push_back( curr_rank );
        }
      }
    }
  }

#ifdef DEBUG
  std::cout << "Rank: " << rank << ", # recvs needed = " << senders.size() << ", senders: ";
  for ( auto s : senders ) {
    std::cout << s << " ";
  }
  std::cout << std::endl;
  mpi_rc = MPI_Barrier(MPI_COMM_WORLD);
#endif
  

//  // Determine how many messages this process will receive
//  int* local_counts = new int[comm_size];
//  for ( int i=0; i<comm_size; ++i ) {
//    local_counts[i] = 0;
//  }
//  for ( int i=0; i<degree; ++i ) {
//    local_counts[ destinations[i] ]++;
//  }
//  int* global_counts = new int[comm_size];
//  mpi_rc = MPI_Allreduce( local_counts, 
//                          global_counts, 
//                          comm_size, 
//                          MPI_INTEGER, 
//                          MPI_SUM, 
//                          MPI_COMM_WORLD );
//  int n_neighbors = global_counts[ rank ];
//  delete [] local_counts;
//  delete [] global_counts;
//
//#ifdef DEBUG
//  std::cout << "Rank: " << rank << ", # neighbors = " << n_neighbors << std::endl;
//  mpi_rc = MPI_Barrier(MPI_COMM_WORLD);
//#endif

  int in_degree = senders.size();
  
  // Determine split of deterministic vs. non-deterministic receives
  int n_nd_recvs = (int) in_degree * nd_fraction_recvs;
  int n_det_recvs = in_degree - n_nd_recvs; 

  // Send and receive buffers
  char* send_buffer, *det_recv_buffer, *nd_recv_buffer;
  double* double_send_buffer, *double_det_recv_buffer, *double_nd_recv_buffer;
  
  // Allocate requests
  MPI_Request * send_reqs = new MPI_Request[ degree ];
  MPI_Request * det_recv_reqs = new MPI_Request[ n_det_recvs ];
  MPI_Request * nd_recv_reqs = new MPI_Request[ n_nd_recvs  ];
  
  if(compute) {
    // Allocate send and receive buffers 
    double_send_buffer = (double*) malloc (degree * msg_size * sizeof(double));
    double_det_recv_buffer = (double*) malloc (n_det_recvs * msg_size * sizeof(double));
    double_nd_recv_buffer = (double*) malloc (n_nd_recvs * msg_size * sizeof(double));
    std::default_random_engine generator(seed);
    std::uniform_real_distribution<double> unif_rand(min, max);
    for(int j=0; j<degree*msg_size; j++) {
      double_send_buffer[j] = unif_rand(generator);
    }

    // Post deterministic receives
    for (int j = 0; j < n_det_recvs; j++) {
      MPI_Irecv( &double_det_recv_buffer[j * msg_size], 
                 msg_size, 
                 MPI_DOUBLE, 
                 senders[j], 
                 iter,
                 MPI_COMM_WORLD, 
                 &det_recv_reqs[j] );
    }
    
    // Post non-deterministic receives
    for (int j = 0; j < n_nd_recvs; j++) {
      MPI_Irecv( &double_nd_recv_buffer[j * msg_size], 
                 msg_size, 
                 MPI_DOUBLE, 
                 MPI_ANY_SOURCE, 
                 iter,
                 MPI_COMM_WORLD, 
                 &nd_recv_reqs[j] );
    }

    // Post sends
    for (int j = 0; j < degree; j++) {
      MPI_Isend( &double_send_buffer[j * msg_size], 
                 msg_size, 
                 MPI_DOUBLE, 
                 destinations[j], 
                 iter,
                 MPI_COMM_WORLD, 
                 &send_reqs[j] );
    } 
  } else {
    // Allocate send and receive buffers 
    send_buffer = (char*) malloc (degree * msg_size * sizeof(char));
    det_recv_buffer = (char*) malloc (n_det_recvs * msg_size * sizeof(char));
    nd_recv_buffer = (char*) malloc (n_nd_recvs * msg_size * sizeof(char));

    // Post deterministic receives
    for (int j = 0; j < n_det_recvs; j++) {
      MPI_Irecv( &det_recv_buffer[j * msg_size], 
                 msg_size, 
                 MPI_CHAR, 
                 senders[j], 
                 iter,
                 MPI_COMM_WORLD, 
                 &det_recv_reqs[j] );
    }
    
    // Post non-deterministic receives
    for (int j = 0; j < n_nd_recvs; j++) {
      MPI_Irecv( &nd_recv_buffer[j * msg_size], 
                 msg_size, 
                 MPI_CHAR, 
                 MPI_ANY_SOURCE, 
                 iter,
                 MPI_COMM_WORLD, 
                 &nd_recv_reqs[j] );
    }

    // Post sends
    for (int j = 0; j < degree; j++) {
      MPI_Isend( &send_buffer[j * msg_size], 
                 msg_size, 
                 MPI_CHAR, 
                 destinations[j], 
                 iter,
                 MPI_COMM_WORLD, 
                 &send_reqs[j] );
    } 
  }
  
  // Complete sends
  MPI_Waitall(degree, &send_reqs[0], MPI_STATUSES_IGNORE);

  // Complete deterministic recvs
  MPI_Status det_recv_status;
  for ( int i=0; i<n_det_recvs; ++i ) {
    mpi_rc = MPI_Wait( &det_recv_reqs[i], &det_recv_status );
    std::cout << "(DETERMINISTIC) Rank: " << rank << " received from: " << det_recv_status.MPI_SOURCE << std::endl;
  }

  // Complete non-deterministic recvs
  MPI_Status nd_recv_status;
  for ( int i=0; i<n_nd_recvs; ++i ) {
    mpi_rc = MPI_Wait( &nd_recv_reqs[i], &nd_recv_status );
    std::cout << "(NON-DETERMINISTIC) Rank: " << rank << " received from: " << nd_recv_status.MPI_SOURCE << std::endl;
  }

  if(compute) {
    double sum = 0.0f;
    double* compute_buffer = (double*) malloc(sizeof(double)*(n_det_recvs+n_nd_recvs));
    // Compute elementwise multiplication
    for(int i=0; i<n_det_recvs; i++) {
      compute_buffer[i] = double_det_recv_buffer[i]*double_det_recv_buffer[i];
    }
    for(int i=n_det_recvs; i<n_nd_recvs+n_det_recvs; i++) {
      compute_buffer[i] = double_nd_recv_buffer[i]*double_nd_recv_buffer[i];
    }
    // Inner product
    for(int i=0; i<n_det_recvs+n_nd_recvs; i++) {
      sum += compute_buffer[i];
    }
    // Compute prefix sum
    for(int i=1; i<n_det_recvs+n_nd_recvs; i++) {
      compute_buffer[i] = compute_buffer[i] + compute_buffer[i-1];
    }
    // Square values
    for(int i=0; i<n_det_recvs+n_nd_recvs; i++) {
      compute_buffer[i] *= compute_buffer[i];
    }
    // Normalize
    double max = compute_buffer[0];
    for(int i=0; i<n_det_recvs+n_nd_recvs; i++) {
      if(std::abs(compute_buffer[i]) > max)
        max = std::abs(compute_buffer[i]);
    }
    for(int i=0; i<n_det_recvs+n_nd_recvs; i++) {
      compute_buffer[i] = compute_buffer[i]/max;
    }
    // Reduction
    for(int i=0; i<n_det_recvs+n_nd_recvs; i++) {
      sum += compute_buffer[i];
    }
    double g_sum = 0.0;
    MPI_Reduce(&sum, &g_sum, 1, MPI_DOUBLE, MPI_SUM, 0, MPI_COMM_WORLD);
    if(rank == 0) {
      std::cout.precision(std::numeric_limits<double>::max_digits10);
      std::cout << "Iteration: " << iter << " Computed: " << g_sum  << std::endl;
    }

    free(double_send_buffer);
    free(double_det_recv_buffer);
    free(double_nd_recv_buffer);
    free(compute_buffer);
  } 

  //MPI_Status recv_statuses[ n_neighbors ];
  //MPI_Waitall(n_neighbors, &recv_reqs[0], &recv_statuses[0]);
}

