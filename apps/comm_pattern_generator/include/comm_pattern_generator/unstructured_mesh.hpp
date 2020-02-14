#ifndef COMM_PATTERN_GENERATOR_UNSTRUCTURED_MESH_H
#define COMM_PATTERN_GENERATOR_UNSTRUCTURED_MESH_H

#include <mpi.h>

void comm_pattern_unstructured_mesh( MPI_Comm comm, bool deterministic );
void comm_pattern_unstructured_mesh_non_deterministic( MPI_Comm comm );
void comm_pattern_unstructured_mesh_deterministic( MPI_Comm comm );

int coords_to_rank( int x_coord, int y_coord, int z_coord, int n_procs_x, int n_procs_y, int n_procs_z );
int wrap( int x, int n_procs );

#endif
