#!/usr/bin/env python3

import pprint

import numpy as np

def levenshtein_dist(obs_order, ref_order):
    assert(len(obs_order) == len(ref_order))
    n = len(obs_order)
    mat = np.zeros((n+1, n+1))
    for i in range(1, n+1):
        mat[i][0] = i
    for i in range(1, n+1):
        mat[0][i] = i
    for i in range(1, n+1):
        for j in range(1, n+1):
            if obs_order[i-1] == ref_order[j-1]:
                sub_cost = 0
            else:
                sub_cost = 1
            mat[i][j] = min( [ mat[i-1][j] + 1,
                               mat[i][j-1] + 1,
                               mat[i-1][j-1] + sub_cost 
                             ]
                           )
    return mat[n][n]


def permutation_encoding_size(obs_order):
    return levenshtein_dist(obs_order, sorted(obs_order))


if __name__ == "__main__":
    #obs_order = [0, 3, 2, 1, 4, 7, 5, 6]
    obs_order = [1, 2, 0]
    d = permutation_encoding_size(obs_order)
    print(d)
