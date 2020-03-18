#!/usr/bin/env python3

import argparse
import glob
import re
import pprint


class mesh_refine_event(object):
    def __init__(self, timestep, load_balance_events):
        self._ts = timestep
        self._lb_events = load_balance_events
        self._begin_timestamp = None
        self._end_timestamp = None
        self._set_timestamps()
        self._total_recv = 0
        self._total_sent = 0
        self._rank_to_total_sent = {}
        self._set_total_block_traffic()

    def _set_timestamps(self):
        n_lb_events = len(self._lb_events)
        # Get timestamp from first load balance event
        self._begin_timestamp = self._lb_events[0].wtime()
        # Get timestamp from last load balance event
        self._end_timestamp = self._lb_events[n_lb_events-1].wtime()

    def _set_total_block_traffic(self):
        for _,lb_event in self._lb_events.items():
            self._total_recv += lb_event.total_blocks_received()
            for dst_rank,n_blocks in lb_event.rank_to_sent().items():
                self._total_sent += n_blocks
                if dst_rank not in self._rank_to_total_sent:
                    self._rank_to_total_sent[dst_rank] = n_blocks
                else:
                    self._rank_to_total_sent[dst_rank] += n_blocks

    def __repr__(self):
        repr_str = "Mesh Refinement Event at Time Step: {}\n".format(self._ts)
        repr_str += "\tStart Time: {}\n".format(self._begin_timestamp)
        repr_str += "\tEnd Time: {}\n".format(self._end_timestamp)
        repr_str += "\tTotal Blocks Received: {}\n".format(self._total_recv)
        repr_str += "\tTotal Blocks Sent: {}\n".format(self._total_sent)
        repr_str += "\tRank-to-Sent-Blocks:\n"
        for dst_rank,n_blocks in self._rank_to_total_sent.items():
             repr_str += "\t\tSent {} blocks to rank {}\n".format(n_blocks,dst_rank)
        return repr_str

    def __str__(self):
        return self.__repr__()

class load_balance_event(object):
    def __init__(self, idx, timestamp, imbalance, rank_to_sent_blocks, blocks_received):
        # An index indicating which load balancing event this was during its
        # containing mesh refinement event
        self._idx = idx
        # Wall timestamp 
        self._wtime = timestamp
        # The imbalance value that triggered this load balance event
        self._imbalance = imbalance
        # Maps destination processes to num. blocks sent by this process
        self._rank_to_sent = rank_to_sent_blocks
        # Total num. blocks received
        self._n_blocks_recv = blocks_received
        self._n_blocks_sent = 0
        self._set_n_blocks_sent()

    def _set_n_blocks_sent(self):
        self._n_blocks_sent = sum(self._rank_to_sent.values())

    def total_blocks_sent(self):
        return sum(self._n_blocks_sent)

    def total_blocks_received(self):
        return self._n_blocks_recv
    
    def rank_to_sent(self):
        return self._rank_to_sent

    def wtime(self):
        return self._wtime

    def __repr__(self):
        repr_str = "Load Balance Event {}:\n".format(self._idx)
        repr_str += "\tImbalance: {}\n".format(self._imbalance)
        repr_str += "\tTimestamp: {}\n".format(self._wtime)
        repr_str += "\t# Blocks Received: {}\n".format(self._n_blocks_recv)
        repr_str += "\t# Blocks Sent: {}\n".format(self._n_blocks_sent)
        repr_str += "\tRank-to-Sent-Blocks:\n"
        for dst_rank,n_blocks in self._rank_to_sent.items():
            repr_str += "\t\tSent {} blocks to rank {}\n".format(n_blocks,dst_rank)
        return repr_str

    def __str__(self):
        return self.__repr__()

def load_logfile(path):
    with open(path,"r") as infile:
        return infile.readlines()

def clean_raw_lines(logfile_raw_lines):
    stripped = [ x.strip() for x in logfile_raw_lines ]
    tab_pattern = re.compile(r"[\t]+")
    # sub call replaces tabs with whitespace
    # join reduces all sequences of multiple whitespace to single
    #cleaned = [ "".join(tab_pattern.sub(" ", x).split()) for x in stripped ]
    cleaned = [ tab_pattern.sub(" ", x) for x in stripped ]
    return cleaned

def get_timestep_lines( lines ):
    pattern = re.compile("^Time step: \d+$")
    timestep_lines = []
    for i in range(len(lines)):
        if pattern.match(lines[i]):
            timestep_lines.append(i)
    return timestep_lines

def get_timestep_from_line( line ):
    non_decimal = re.compile(r"[^\d.]+")
    return int(non_decimal.sub("", line))

def get_timestep_bounds( lines ):
    timestep_lines = get_timestep_lines(lines)
    n_mesh_refinements = len(timestep_lines)
    n_lines = len(lines)
    ts_to_bounds = {}
    for i in range(n_mesh_refinements):
        ts_line = timestep_lines[i]
        # Case 1: First pre-execution mesh refinement
        # Grab all lines up to the timestep line
        if i == 0:
            ts_to_bounds[0] = (0, ts_line-1)
        # Case 2: Last mesh refinement
        # Grab all lines after the timestep line
        elif i == n_mesh_refinements - 1:
            ts = get_timestep_from_line(lines[ts_line])
            ts_to_bounds[ts] = (ts_line, n_lines-1)
        # Case 3: Interior mesh refinements
        else:
            ts = get_timestep_from_line(lines[ts_line])
            ts_to_bounds[ts] = ( ts_line, timestep_lines[i+1]-1 )
    return ts_to_bounds

def group_by_timestep( lines ):
    timestep_to_events = { 0:None }
    timestep_to_bounds = get_timestep_bounds( lines )
    timestep_to_lines = {ts:lines[bounds[0]:bounds[1]+1] for ts,bounds in timestep_to_bounds.items()}
    return timestep_to_lines


def get_load_balance_event_start_lines(lines):
    imbalance_pattern = re.compile("^Imbalance ratio: [\d\.]+$")
    load_balance_start_lines = []
    for i in range(len(lines)):
        if imbalance_pattern.match(lines[i]):
            load_balance_start_lines.append(i)
    return load_balance_start_lines

def get_load_balance_event_bounds(lines):
    start_lines = get_load_balance_event_start_lines(lines)
    curr_event_idx = 0
    event_idx_to_bounds = {}
    n_lines = len(lines)
    for i in range(len(start_lines)):
        # Case 1: Get last load balance event
        if i == len(start_lines)-1:
            bounds = ( start_lines[i], n_lines-1 )
        # Case 2: All others
        else:
            bounds = ( start_lines[i], start_lines[i+1]-1 )
        event_idx_to_bounds[ curr_event_idx ] = bounds
        curr_event_idx += 1
    return event_idx_to_bounds


def get_timestamp_from_line(line):
    non_decimal = re.compile(r"[^\d.]+")
    return float(non_decimal.sub("", line))

def get_imbalance_from_line(line):
    non_decimal = re.compile(r"[^\d.]+")
    return float(non_decimal.sub("", line))

def get_recv_blocks_from_line(line):
    return [ int(s) for s in line.split() if s.isdigit() ][-1]

def get_sent_blocks_from_line(line):
    rank, n_blocks, dst = [ int(s) for s in line.split() if s.isdigit() ]
    return dst,n_blocks

def make_lb_event(lb_idx, lines):
    timestamp_pattern = re.compile("^Timestamp: [\d\.]+$")
    imbalance_pattern = re.compile("^Imbalance ratio: [\d\.]+$")
    sent_blocks_pattern = re.compile("^Rank \d+ sent \d+ blocks to \d+$")
    recv_blocks_pattern = re.compile("^Total: Rank \d+ sent: \d+ recv: \d+$")
    rank_to_sent_blocks = {}
    timestamp = None
    imbalance = None
    recv_blocks = None
    for x in lines:
        if timestamp_pattern.match(x):
            timestamp = get_timestamp_from_line(x)
        elif imbalance_pattern.match(x):
            imbalance = get_imbalance_from_line(x)
        elif recv_blocks_pattern.match(x):
            recv_blocks = get_recv_blocks_from_line(x)
        elif sent_blocks_pattern.match(x):
            rank,sent_blocks = get_sent_blocks_from_line(x)
            rank_to_sent_blocks[rank] = sent_blocks

    
    lb_event = load_balance_event(lb_idx, timestamp, imbalance, rank_to_sent_blocks, recv_blocks)
    return lb_event

def get_load_balance_events(lines):
    lb_event_to_bounds = get_load_balance_event_bounds(lines)
    lb_event_to_lines = {lb:lines[bounds[0]:bounds[1]+1] for lb,bounds in lb_event_to_bounds.items()}
    lb_events = {lb:make_lb_event(lb, lines) for lb,lines in lb_event_to_lines.items()}
    return lb_events

def parse_event_lines( event_lines ):
    lb_events = get_load_balance_events( event_lines )
    return lb_events

def parse_logfile(logfile_raw_lines):
    cleaned = clean_raw_lines( logfile_raw_lines )
    timestep_to_event_lines = group_by_timestep( cleaned )
    timestep_to_events = {ts:parse_event_lines(lines) for ts,lines in timestep_to_event_lines.items()}
    for ts,lb_events in timestep_to_events.items():
        mr_event = mesh_refine_event(ts, lb_events)
        print(mr_event)
        print()
    exit()

def load_single_run(trace_dir):
    pattern = re.compile("^[\w\/]+miniAMR_\d+\.log$")
    candidates = glob.glob(trace_dir+"/*.log")
    logfile_paths = filter(lambda x: pattern.match(x), candidates)
    logfile_raw_lines = [ load_logfile(x) for x in logfile_paths ]
    logfile_data = [ parse_logfile(x) for x in logfile_raw_lines ]
    return logfile_data


def analyze_single_run(trace_dir):
    logs = load_single_run( trace_dir )
    pprint.pprint(logs[0])
    exit()


def main(args):
    trace_dir = args.trace_dir
    analyze_single_run(trace_dir)


if __name__ == "__main__":
    desc = ""
    parser = argparse.ArgumentParser(description=desc)
    parser.add_argument("trace_dir", 
                        help="Directory containing traces from a single run")

    args = parser.parse_args()
    main(args)
