#include "unstructured_mesh.hpp"

#include <mpi.h>
#include <cstdio>
#include <cstdlib>
#include <cmath>
#include <ctime>
#include <vector>
#include <unordered_set>
#include <iostream>

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

  std::cout << "Rank: " << rank << " (" << x_coord << ", " << y_coord << ", " << z_coord << ")" << std::endl;
  
  mpi_rc = MPI_Barrier( MPI_COMM_WORLD );
  
  // Determine number of destinations
  std::srand( std::time(0) % rank );
  int range = max_deg - min_deg;
  // Guarantee range of at least one
  (range > 0) ? range : 1;
  int degree = min_deg + ( std::rand() % range );

  //std::cout << "Rank: " << rank << ", # destinations = " << degree << std::endl;

  // Determine who this process's destinations are
  std::unordered_set<int> destination_set;
  std::vector<int> destinations;
  for (int i=0; i<degree; ++i ) {
    int destination_rank = rank;
    // Randomize next destination until it isn't own rank
    while (true) {
      int destination_x_coord = wrap( x_coord, (((std::rand() % 2) ? -1 : 1) * (std::rand() % max_dist)));
      int destination_y_coord = wrap( y_coord, (((std::rand() % 2) ? -1 : 1) * (std::rand() % max_dist)));
      int destination_z_coord = wrap( z_coord, (((std::rand() % 2) ? -1 : 1) * (std::rand() % max_dist)));
      destination_rank = coords_to_rank( destination_x_coord, destination_y_coord, 
                                      destination_z_coord, n_procs_x, n_procs_y );
      // Only accept a destination if it is:
      // 1. Not self rank
      // 2. Not already a destination
      //if ( destination_rank != rank and destinations.find(destination_rank) == destinations.end() ) 
      //
      if ( rank < n_procs_x + 1 ) {
        break;
      } 
      else {
        if ( destination_rank != rank and destination_set.find(destination_rank) == destination_set.end() ) {
        //if ( destination_set.find(destination_rank) == destination_set.end() ) {
          destination_set.insert( destination_rank );
          break;
        }
      }
    }
    destinations.push_back( destination_rank );
  }
  std::cout << "Rank: " << rank << ", # destinations = " << degree << ", destinations: ";
  for ( auto n : destinations ) {
    std::cout << n << " ";
  }
  std::cout << std::endl;

}

