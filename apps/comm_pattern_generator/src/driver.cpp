#include <mpi.h>
#include <cstdio>
#include <cstdlib>
#include <string>
#include <iostream>

#include "configuration.hpp"
#include "debug.hpp"

// Communication patterns
#include "naive_reduce.hpp"
#include "amg2013.hpp"
#include "unstructured_mesh.hpp"
#include "mini_mcb.hpp"

int main( int argc, char** argv )
{
  int mpi_rc, rank, comm_size;
  mpi_rc = MPI_Init( &argc, &argv );
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

#ifdef DEBUG
  if ( rank == 0 ) {
    config.print();
  }
#endif

  // Iterate over the comm patterns
  auto comm_pattern_seq = config.get_comm_pattern_seq();
  mpi_rc = MPI_Barrier( MPI_COMM_WORLD );
  for ( auto comm_pattern : comm_pattern_seq ) {
    auto pattern_name = comm_pattern.pattern_name;
    auto nd_fraction = comm_pattern.nd_fraction;
    auto n_iters = comm_pattern.n_iters;
#ifdef DEBUG
    if ( rank == 0 ) {
      std::cout << "Communication Pattern: " << pattern_name 
                << " Non-Determinism Fraction: " << nd_fraction
                << " # iterations: " << n_iters
                << std::endl;
    }
#endif
    for ( int i=0; i<n_iters; ++i ) {
      if ( pattern_name == "naive_reduce" ) {
        auto msg_size = std::stoi( comm_pattern.params.at("msg_size") );
        comm_pattern_naive_reduce( i, nd_fraction, msg_size, false );
      } 
      else if ( pattern_name == "amg2013" ) {
        auto msg_size = std::stoi( comm_pattern.params.at("msg_size") );
        comm_pattern_amg2013( i, nd_fraction, msg_size );
      }
      else if ( pattern_name == "unstructured_mesh" ) {
        auto nd_fraction_recvs = nd_fraction;
        auto nd_fraction_neighbors = std::stod( comm_pattern.params.at("nd_fraction_neighbors") );
        auto n_procs_x = std::stoi( comm_pattern.params.at("n_procs_x") );
        auto n_procs_y = std::stoi( comm_pattern.params.at("n_procs_y") );
        auto n_procs_z = std::stoi( comm_pattern.params.at("n_procs_z") );
        auto min_deg = std::stoi( comm_pattern.params.at("min_deg") );
        auto max_deg = std::stoi( comm_pattern.params.at("max_deg") );
        auto max_dist = std::stoi( comm_pattern.params.at("max_dist") );
        auto msg_size = std::stoi( comm_pattern.params.at("msg_size") );
        comm_pattern_unstructured_mesh( i, nd_fraction_neighbors, nd_fraction_recvs,
                                        n_procs_x, n_procs_y, n_procs_z, 
                                        min_deg, max_deg, max_dist, msg_size );
      }
      else if ( pattern_name == "mini_mcb" ) {
        auto n_sub_iters = std::stoi( comm_pattern.params.at("n_sub_iters") );
        auto n_grid_steps = std::stoi( comm_pattern.params.at("n_grid_steps") );
        auto n_reduction_steps = std::stoi( comm_pattern.params.at("n_reduction_steps") );
        auto interleave_nd_iters = std::stoi( comm_pattern.params.at("interleave_nd_iters") );
        comm_pattern_mini_mcb( n_sub_iters, n_grid_steps, n_reduction_steps, nd_fraction, interleave_nd_iters );
      }
    }
    mpi_rc = MPI_Barrier( MPI_COMM_WORLD );
  }

  mpi_rc = MPI_Finalize();
  return EXIT_SUCCESS;
}
