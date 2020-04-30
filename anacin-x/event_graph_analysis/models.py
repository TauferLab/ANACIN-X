#!/usr/bin/env python3

import argparse

# Imports for training SVRs
from sklearn.model_selection import train_test_split, KFold, GridSearchCV
from sklearn import svm
from sklearn.metrics import accuracy_score, mean_squared_error

import pprint

import re
import os
import glob
import json
import numpy as np

# Import event graph utilities
import sys
sys.path.append(".")
sys.path.append("..")
import pickle as pkl


class model_manager(object):
    def __init__(self, kernel_matrices, graph_labels, target, output_path, n_folds, n_repeats):
        self._kernel_matrices = kernel_matrices
        self._graph_labels = graph_labels
        self._target = target
        self._output_path = output_path
        self._n_folds = n_folds
        self._n_repeats = n_repeats
        self._kernel_to_model = {}

    def build_models(self):
        for kernel,mat in self._kernel_matrices.items():
            self._build_model(kernel, mat)

    def _get_k_train(self, k_mat, train_indices):
        n = len(train_indices)
        k_train = np.zeros((n,n))
        for i in range(n):
            for j in range(n):
                k_train[i][j] = k_mat[train_indices[i]][train_indices[j]]
        return k_train

    def _get_k_test(self, k_mat, train_indices, test_indices):
        n = len(train_indices)
        m = len(test_indices)
        k_test = np.zeros((m,n))
        for i in range(m):
            for j in range(n):
                k_test[i][j] = k_mat[test_indices[i]][train_indices[j]]
        return k_test

    def _build_model(self, kernel, k_mat):
        print("Build model for kernel: {}".format(kernel))
        print("Predicting: {}".format(self._target))
        target = [ y[self._target] for y in self._graph_labels ]
        n_graphs = len(self._graph_labels)
        for repeat_idx in range(self._n_repeats):
            fold_to_results = {}
            kf = KFold(n_splits=self._n_folds, random_state=repeat_idx, shuffle=True)
            for split_idx, (train_indices, test_indices) in enumerate(kf.split(range(n_graphs))):
                # Get test-train split
                y_train = [ target[i] for i in train_indices ]
                y_test = [ target[i] for i in test_indices ]
                k_train = self._get_k_train(k_mat, train_indices )
                k_test = self._get_k_test(k_mat, train_indices, test_indices )
                
                # Initialize SVR model
                curr_svr = svm.SVR(kernel="precomputed")
                
                # Train SVR model
                curr_svr.fit(k_train, y_train)

                # Predict
                y_pred = curr_svr.predict(k_test)
                
                # Record model params and perf
                relative_errors = []
                for tv,pv in zip(y_test, y_pred):
                    rel_error = np.abs(tv - pv)/tv
                    relative_errors.append(rel_error)
                print("Split: {}".format(split_idx))
                print("Min Rel. Error: {}".format(min(relative_errors)))
                print("Median Rel. Error: {}".format(np.median(relative_errors)))
                print("Max Rel. Error: {}".format(max(relative_errors)))
                print()
                
                results = { "true" : y_test, "pred" : y_pred, "svr_params" : {} }
                fold_to_results[split_idx] = results
            exit()


    




def main(kernel_matrices_path, graph_labels_path, target, output_path, n_folds, n_repeats):
    
    with open(kernel_matrices_path, "rb") as infile:
        kernel_to_matrices = pkl.load(infile)
    
    with open(graph_labels_path, "rb") as infile:
        graph_labels = pkl.load(infile)

    mm = model_manager(kernel_to_matrices, graph_labels, target, output_path, n_folds, n_repeats)
    mm.build_models()

    #kernel_to_results = build_models(kernel_to_matrices)


if __name__ == "__main__":
    desc = ""
    parser = argparse.ArgumentParser(description=desc)
    parser.add_argument("--kernel_matrices", required=True, help="Path to pickle file containing graph kernel matrices")
    parser.add_argument("--graph_labels", required=True, help="Path to pickle file containing mapping from graph indices to graph class labels")
    parser.add_argument("--predict", required=True, help="Run parameter to predict")
    parser.add_argument("--output", required=False, default=None, help="Path to write pickled results dict to")
    parser.add_argument("--n_folds", required=False, type=int, default=10, help="Number of folds for k-fold cross-validation")
    parser.add_argument("--n_repeats", required=False, type=int, default=10, help="Number of times to repeat cross-validation")
    args = parser.parse_args()
    main(args.kernel_matrices,
         args.graph_labels,
         args.predict,
         args.output,
         args.n_folds,
         args.n_repeats)

