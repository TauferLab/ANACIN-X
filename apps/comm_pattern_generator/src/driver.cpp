#include <mpi.h>
#include <cstdio>
#include <cstdlib>
#include <string>
#include <iostream>

#include "configuration.hpp"
#include "naive_reduce.hpp"
#include "amg2013.hpp"
#include "unstructured_mesh.hpp"

int main( int argc, char** argv )
{
  int mpi_rc, rank, comm_size;
  mpi_rc = MPI_Init( nullptr, nullptr );
  mpi_rc = MPI_Comm_rank( MPI_COMM_WORLD, &rank );
  mpi_rc = MPI_Comm_size( MPI_COMM_WORLD, &comm_size );


  // Ingest configuration
  Configuration config;
  if ( rank == 0 ) {
    std::string config_path( argv[1] );
    config = Configuration(config_path);
    broadcast_config( config );
  } else {
    broadcast_config( config );
  }

  if ( rank == 0 ) {
    config.print();
  }

  // Iterate over the comm patterns
  auto comm_pattern_seq = config.get_comm_pattern_seq();
  mpi_rc = MPI_Barrier( MPI_COMM_WORLD );
  for ( auto comm_pattern : comm_pattern_seq ) {
    // First, split comms based on desired fraction of non-deterministic 
    // communication
    auto pattern_name = comm_pattern.pattern_name;
    auto nd_fraction = comm_pattern.nd_fraction;
    auto n_iters = comm_pattern.n_iters;
    if ( rank == 0 ) {
      std::cout << "Communication Pattern: " << pattern_name 
                << " Non-Determinism Fraction: " << nd_fraction
                << " # iterations: " << n_iters
                << std::endl;
    }
    //int cutoff_rank = comm_size * nd_fraction;
    //if ( rank == 0 ) {
    //  std::cout << "Ranks up to " << cutoff_rank << " will execute non-deterministic version of pattern" << std::endl;
    //}
    //int color;
    //if ( rank < cutoff_rank ) {
    //  color = 0;
    //} else {
    //  color = 1;
    //}
    //MPI_Comm pattern_comm;
    //mpi_rc = MPI_Comm_split( MPI_COMM_WORLD, color, rank, &pattern_comm);
    // Do this pattern for specified number of iterations
    for ( int i=0; i<n_iters; ++i ) {
      if ( pattern_name == "naive_reduce" ) {
        auto msg_size = comm_pattern.params.at("msg_size");
        comm_pattern_naive_reduce( i, nd_fraction, msg_size, false );
      } 
      else if ( pattern_name == "amg2013" ) {
        auto msg_size = comm_pattern.params.at("msg_size");
        comm_pattern_amg2013( i, nd_fraction, msg_size );
      }
      else if ( pattern_name == "unstructured_mesh" ) {
        auto n_procs_x = comm_pattern.params.at("n_procs_x");
        auto n_procs_y = comm_pattern.params.at("n_procs_y");
        auto n_procs_z = comm_pattern.params.at("n_procs_z");
        auto min_deg = comm_pattern.params.at("min_deg");
        auto max_deg = comm_pattern.params.at("max_deg");
        auto max_dist = comm_pattern.params.at("max_dist");
        auto msg_size = comm_pattern.params.at("msg_size");
        comm_pattern_unstructured_mesh( i, nd_fraction, n_procs_x, n_procs_y, 
                                        n_procs_z, min_deg, max_deg, max_dist, 
                                        msg_size );
      }
      //mpi_rc = MPI_Barrier( MPI_COMM_WORLD );
    }
    //mpi_rc = MPI_Comm_free( &pattern_comm );
    mpi_rc = MPI_Barrier( MPI_COMM_WORLD );
  }

  mpi_rc = MPI_Finalize();
  return EXIT_SUCCESS;
}
