import igraph
import argparse

def main(graph_path):
    graph = igraph.read(graph_path)
    print(len(graph.vs[:]))
    print(len(graph.es[:]))

if __name__ == '__main__':
    desc = ""
    parser = argparse.ArgumentParser(description=desc)
    parser.add_argument("graph_path",
                        help="Path to a GraphML file representing an event graph")
    args = parser.parse_args()
    main(args.graph_path)
