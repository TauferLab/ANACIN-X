#ifndef MINI_MCB_H
#define MINI_MCB_H

void comm_pattern_mini_mcb( int n_iters, int n_grid_steps, int n_reduction_steps, double nd_fraction, int interleave, bool compute=false, double min=0.0, double max = 1.0, int seed=0 );
void shuffle(int* array, int size);
int is_finished();
void bin_reduction_init();
int bin_reduction_start(int non_deterministic);
int bin_reduction_end(int non_deterministic);
void bin_reduction_finalize();
void do_work();
void neighbor_communication_init();
void neighbor_communication(int non_deterministic);
void neighbor_communication_finalize();
int compute_global_hash();
double get_runtime();


#endif
