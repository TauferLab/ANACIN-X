#ifndef COMM_PATTERN_GENERATOR_UNSTRUCTURED_MESH_H
#define COMM_PATTERN_GENERATOR_UNSTRUCTURED_MESH_H

#include <mpi.h>

void comm_pattern_unstructured_mesh( int iter, double nd_fraction_neighbors, double nd_fraction_recvs,
                                     int n_procs_x, int n_procs_y, int n_procs_z, 
                                     int min_deg, int max_deg, int max_dist, int msg_size );

int coords_to_rank( int x_coord, int y_coord, int z_coord, int n_procs_x, int n_procs_y, int n_procs_z );
int wrap( int x, int n_procs );

#endif
