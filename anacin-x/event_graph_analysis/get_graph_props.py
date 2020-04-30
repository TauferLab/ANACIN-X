#!/usr/bin/env python3

import argparse
import igraph
import sys
sys.path.append(".")
sys.path.append("..")
from event_graph_analysis.utilities import read_graph

def main(graph_path):
    g = read_graph(graph_path)
    n_vertices = g.vcount()
    n_edges = g.ecount()
    print("# Vertices: {}".format(n_vertices))
    print("# Edges: {}".format(n_edges))

if __name__ == "__main__":
    desc = ""
    parser = argparse.ArgumentParser(description=desc)
    parser.add_argument("graph", help="")
    args = parser.parse_args()
    main(args.graph)
