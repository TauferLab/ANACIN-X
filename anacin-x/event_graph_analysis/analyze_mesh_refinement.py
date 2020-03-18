#!/usr/bin/env python3

import argparse
import glob
import re
import pprint

import igraph

class global_mesh_refine_event(object):
    def __init__(self, rank_to_local_mesh_refine_event, make_graph=False):
        self._rank_to_local_mre = rank_to_local_mesh_refine_event
        self._ts = None
        self._set_timestep()
        self._begin_timestamp = None
        self._end_timestamp = None
        self._elapsed_time = None
        self._set_timestamps()
        self._total_recv = 0
        self._total_sent = 0
        self._total_block_traffic = None
        self._channel_to_traffic = {}
        self._set_total_block_traffic()
        self._block_traffic_graph = None
        if make_graph:
            self._make_block_traffic_graph()

    def _set_timestep(self):
        rank_to_timestep = {rank:mre.timestep() for rank,mre in self._rank_to_local_mre.items()}
        assert(len(set(rank_to_timestep.values())) == 1)
        self._ts = rank_to_timestep[0]

    def _set_timestamps(self):
        rank_to_begin_ts = {rank:mre.begin_timestamp() for rank,mre in self._rank_to_local_mre.items()}
        rank_to_end_ts = {rank:mre.end_timestamp() for rank,mre in self._rank_to_local_mre.items()}
        self._begin_timestamp = min(rank_to_begin_ts.values())
        self._end_timestamp = max(rank_to_end_ts.values())
        self._elapsed_time = self._end_timestamp - self._begin_timestamp
    
    def _set_total_block_traffic(self):
        for src_rank,mre in self._rank_to_local_mre.items():
            self._total_recv += mre.total_recv()
            for dst_rank,n_blocks in mre.rank_to_blocks_sent().items():
                self._total_sent += n_blocks
                channel = (src_rank, dst_rank)
                if channel not in self._channel_to_traffic:
                    self._channel_to_traffic[channel] = n_blocks
                else:
                    self._channel_to_traffic[channel] += n_blocks
        assert(self._total_recv == self._total_sent)
        self._total_block_traffic = self._total_recv

    def __repr__(self):
        repr_str = "Global Mesh Refinement Event at Time Step: {}\n".format(self._ts)
        repr_str += "\tStart Time: {}\n".format(self._begin_timestamp)
        repr_str += "\tEnd Time: {}\n".format(self._end_timestamp)
        repr_str += "\tElapsed Time: {}\n".format(self._elapsed_time)
        repr_str += "\tTotal Block Traffic: {} blocks\n".format(self._total_block_traffic)
        repr_str += "\tChannel-to-Sent-Blocks:\n"
        for channel,n_blocks in self._channel_to_traffic.items():
             repr_str += "\t\tSent {} blocks to in channel {}\n".format(n_blocks,channel)
        return repr_str

    def __str__(self):
        return self.__repr__()

    def _make_block_traffic_graph(self):
        graph = igraph.Graph(directed=True)
        ranks = set()
        for src_rank,mre in self._rank_to_local_mre.items():
            ranks.add(src_rank)
            for dst_rank in mre.rank_to_blocks_sent().keys():
                ranks.add(dst_rank)
        ranks = sorted(ranks)
        graph.add_vertices(len(ranks))
        graph.vs[:]["rank"] = ranks
        edge_weights = []
        for channel,n_blocks in self._channel_to_traffic.items():
            src_rank, dst_rank = channel
            if src_rank != dst_rank and n_blocks != 0:
                graph.add_edge(src_rank, dst_rank)
                edge_weights.append(n_blocks)
        graph.es[:]["n_blocks"] = edge_weights
        self._block_traffic_graph = graph
        

    def make_plot(self):
        # Build graph if necessary
        if self._block_traffic_graph is None:
            self._make_block_traffic_graph()
        # Normalize edge weights
        max_nb = max(self._block_traffic_graph.es["n_blocks"])
        normalized_nb = [ nb/max_nb for nb in self._block_traffic_graph.es["n_blocks"] ]
        edge_width_scale = 8
        edge_widths = [ nb*edge_width_scale for nb in normalized_nb ]
        # Make plot 
        n_vertices = len(self._block_traffic_graph.vs[:])
        vertex_label_distances = [ 0 ] * n_vertices
        
        layout = self._block_traffic_graph.layout_circle()
        igraph.plot( self._block_traffic_graph, 
                     layout = layout,
                     vertex_label=self._block_traffic_graph.vs[:]["rank"],
                     vertex_label_dist=vertex_label_distances,
                     edge_width=edge_widths,
                     target="miniAMR_run_0_mre_0.png"
                   )



class local_mesh_refine_event(object):
    def __init__(self, timestep, load_balance_events):
        self._ts = timestep
        self._lb_events = load_balance_events
        self._begin_timestamp = None
        self._end_timestamp = None
        self._elapsed_time = None
        self._set_timestamps()
        self._total_recv = 0
        self._total_sent = 0
        self._rank_to_total_sent = {}
        self._set_total_block_traffic()

    def timestep(self):
        return self._ts

    def begin_timestamp(self):
        return self._begin_timestamp
    
    def end_timestamp(self):
        return self._end_timestamp
    
    def rank_to_blocks_sent(self):
        return self._rank_to_total_sent

    def total_recv(self):
        return self._total_recv

    def _set_timestamps(self):
        n_lb_events = len(self._lb_events)
        # Get timestamp from first load balance event
        self._begin_timestamp = self._lb_events[0].wtime()
        # Get timestamp from last load balance event
        self._end_timestamp = self._lb_events[n_lb_events-1].wtime()
        self._elapsed_time = self._end_timestamp - self._begin_timestamp

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
        repr_str = "Local Mesh Refinement Event at Time Step: {}\n".format(self._ts)
        repr_str += "\tStart Time: {}\n".format(self._begin_timestamp)
        repr_str += "\tEnd Time: {}\n".format(self._end_timestamp)
        repr_str += "\tElapsed Time: {}\n".format(self._elapsed_time)
        repr_str += "\tTotal Blocks Received: {}\n".format(self._total_recv)
        repr_str += "\tTotal Blocks Sent: {}\n".format(self._total_sent)
        repr_str += "\tRank-to-Sent-Blocks:\n"
        for dst_rank,n_blocks in self._rank_to_total_sent.items():
             repr_str += "\t\tSent {} blocks to rank {}\n".format(n_blocks,dst_rank)
        return repr_str

    def __str__(self):
        return self.__repr__()

class local_load_balance_event(object):
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
    ts_to_bounds = { 0 : (0, timestep_lines[0]-1) }
    for i in range(n_mesh_refinements):
        ts_line = timestep_lines[i]
        # Case 1: Last mesh refinement
        # Grab all lines after the timestep line
        if i == n_mesh_refinements - 1:
            ts = get_timestep_from_line(lines[ts_line])
            ts_to_bounds[ts] = (ts_line, n_lines-1)
        # Case 2: Interior mesh refinements
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

    
    lb_event = local_load_balance_event(lb_idx, timestamp, imbalance, rank_to_sent_blocks, recv_blocks)
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
    mr_events = []
    for ts,lb_events in timestep_to_events.items():
        mr_event = local_mesh_refine_event(ts, lb_events)
        mr_events.append(mr_event)
    return mr_events


def get_rank_from_path(path):
    return int(path.split("_")[-1].split(".")[0])

def load_single_run(trace_dir):
    pattern = re.compile("^[\w\/]+miniAMR_\d+\.log$")
    candidates = glob.glob(trace_dir+"/*.log")
    logfile_paths = filter(lambda x: pattern.match(x), candidates)
    rank_to_raw_lines = { get_rank_from_path(path):load_logfile(path) for path in logfile_paths }
    rank_to_data = { rank:parse_logfile(lines) for rank,lines in rank_to_raw_lines.items() }
    return rank_to_data


def analyze_single_run(trace_dir):
    rank_to_data = load_single_run( trace_dir )
    
    rank_to_n_mesh_refine_events = {rank:len(data) for rank,data in rank_to_data.items()}
    assert(len(set(rank_to_n_mesh_refine_events.values()))==1)
    
    n_mesh_refine_events = len(rank_to_data[0])
    for i in range(n_mesh_refine_events):
        curr_rank_to_events = {rank:events[i] for rank,events in rank_to_data.items()}
        gmre = global_mesh_refine_event( curr_rank_to_events )
        #print(gmre)
        gmre.make_plot()
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
