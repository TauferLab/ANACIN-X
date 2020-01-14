import numpy as np
import igraph

from utilities import timer

"""
A function to convert a kernel matrix to a distance matrix
For details on similarity -> distance formulat, see [1].
1. Phillips, J.M. and Venkatasubramanian, S., 2011. A gentle introduction to the 
   kernel distance. arXiv preprint arXiv:1103.1625.
"""
#@timer
def convert_to_distance_matrix( kernel_mat ):
    n_rows = len( kernel_mat )
    n_cols = len( kernel_mat[0] )
    assert( n_rows == n_cols )
    dist_mat = np.zeros( ( n_rows, n_cols ) )
    for i in range(n_rows):
        for j in range(n_cols):
            self_similarity = kernel_mat[i][i] + kernel_mat[j][j]
            cross_similarity = 2*kernel_mat[i][j]
            kernel_distance = np.sqrt( self_similarity - cross_similarity )
            dist_mat[i][j] = kernel_distance
    return dist_mat

def flatten_distance_matrix( dist_mat ):
    n_rows = len( dist_mat )
    n_cols = len( dist_mat[0] )
    assert( n_rows == n_cols )
    distances = []
    for i in range( n_rows ):
        for j in range( i, n_cols ):
            distances.append( dist_mat[i][j] )
    return distances
                
    

"""                                                                             
Checks that kernel matrix is eligible to be converted into a distance matrix.   
Specifically, we check that sum of self-similarities for graphs G and G' is     
always greater than 2 * cross-similarity of G and G'                            
"""                                                                             
#@timer                                                                          
def validate_kernel_matrix( kernel_mat, graphs ):                                        
    n_graphs = len(kernel_mat)                                                           
    for i in range( n_graphs ):                                                 
        for j in range( n_graphs ):                                             
            self_similarity = kernel_mat[i][i] + kernel_mat[j][j]
            cross_similarity = 2*kernel_mat[i][j]                                        
            if self_similarity < cross_similarity:                              
                graph_i = graphs[i]                                             
                graph_j = graphs[j]                                             
                iso = graph_i.isomorphic( graph_j )                             
                if not iso:                                                     
                    err_str = ( "Self-similarity less than cross-similarity for"
                                " non-isomorphic graphs\n")
                    err_str += "K[{}][{}] = {}\n".format(i, i, K[i][i])
                    err_str += "K[{}][{}] = {}\n".format(j, j, K[j][j])
                    err_str += "K[{}][{}] = {}\n".format(i, j, K[i][j])         
                    raise RuntimeError( err_str ) 
