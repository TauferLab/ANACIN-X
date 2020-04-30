#!/usr/bin/env python3

import pprint

import argparse
import re

def parse_rempi_log_line(line):
    parts = [ x.strip() for x in line.split(":") ]
    pid = int(parts[3])
    component = parts[4]
    size = int(parts[5].split()[0]) * 8 # num chars * bytes per char
    return (pid,component,size)

def parse_rempi_log(rempi_log_path):
    pattern = re.compile("^REMPI:DEBUG:[A-Za-z0-9]+:\s+\d+:\s+[A-Za-z0-9-\s]+:\s+\d+\s.+$")
    validation_line_pattern = re.compile("^REMPI:DEBUG:[A-Za-z0-9]+:\s+\d+:\s+validation code:\s+\d+.+$")
    pid_to_record_components = {}
    with open(rempi_log_path, "r") as infile:
        lines = infile.readlines()  
    for line in lines:
        if pattern.match(line) and not validation_line_pattern.match(line):
            pid,component,size = parse_rempi_log_line(line)
            if pid not in pid_to_record_components:
                pid_to_record_components[pid] = {component : size}
            else:
                pid_to_record_components[pid][component] = size
    return pid_to_record_components

def get_pid_to_record_size(pid_to_record_components):
    return {pid:sum(component_to_size.values()) for pid,component_to_size in pid_to_record_components.items()}

def group_by_record_component(pid_to_record_components):
    component_to_sizes = {}
    for pid,component_to_size in pid_to_record_components.items():
        for component,size in component_to_size.items():
            if component not in component_to_sizes:
                component_to_sizes[component] = [ size ]
            else:
                component_to_sizes[component].append(size)
    return component_to_sizes

def get_total_record_size(pid_to_record_components):
    return sum(get_pid_to_record_size(pid_to_record_components).values())


def get_total_record_component_size(component_to_sizes, component='CDC-Encoded Matched-Test Table Size'):
    return {"component":component, "total":sum(component_to_sizes[component])}

def main(rempi_log_path):
    pid_to_record_components = parse_rempi_log(rempi_log_path)
    component_to_size_distribution = group_by_record_component(pid_to_record_components)
    pid_to_total_size = get_pid_to_record_size(pid_to_record_components)
    total = get_total_record_size(pid_to_record_components)
    total_matched_test_table_size = get_total_record_component_size(component_to_size_distribution)
    print(total_matched_test_table_size)
    print(total)

if __name__ == "__main__":
    desc = "Parses recording log output from ReMPI and summarizes recording costs"
    parser = argparse.ArgumentParser(description=desc)
    parser.add_argument("rempi_log_path", help="Path to ReMPI log")
    args = parser.parse_args()
    main(args.rempi_log_path)
