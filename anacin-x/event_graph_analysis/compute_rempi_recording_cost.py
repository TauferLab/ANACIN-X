#!/usr/bin/env python3

import argparse
import igraph


def read_graph( graph_path ):
    graph = igraph.read( graph_path )
    return graph


def get_program_order(event_graph, process_id):
    return event_graph.vs.select(process_id_eq=process_id)

def get_program_orders( event_graph ):
    pids = set(event_graph.vs[:]["process_id"])
    pid_to_order = { pid:get_program_order(event_graph, pid) for pid in pids}
    return pid_to_order


def main(graph_path):
    g = read_graph(graph_path)
    pid_to_order = get_program_orders(g)
    for pid,order in pid_to_order.items():
        received_clocks = []
        for v in order:
            if v["event_type"] == "recv":
                preds = v.predecessors()
                for p in preds:
                    if p["event_type"] == "send":
                        received_clocks.append([p["logical_time"], p["process_id"]])

if __name__ == "__main__":
    desc = "A script to apply ReMPI recording cost vertex attributes and compute total ReMPI recording cost "
    parser = argparse.ArgumentParser(description=desc)
    parser.add_argument("event_graph", 
                        help="Path of event graph file to annotate")
    args = parser.parse_args()

    main(args.event_graph)
