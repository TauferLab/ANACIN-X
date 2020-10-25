import json
import sys

out = {"comm_patterns": []}


if sys.argv[1] == "amg2013":
    nd_frac = 0.0
    for i in range(0, 11):
        out["comm_patterns"].append( {"pattern_name": sys.argv[1],
                                   "n_iters": 1,
                                   "nd_fraction": round(nd_frac, 1),
                                   "params": [
                                       {
                                           "key": "msg_size",
                                           "val": sys.argv[2]
                                       }
                                   ]})
        nd_frac += 0.1
    with open("amg2013_msg_size_{}.json".format(int(sys.argv[2])), 'w+') as f:
        json.dump(out, f, indent=4)

elif sys.argv[1] == "naive_reduce":
    nd_frac = 0.0
    print("e")
    for i in range(0, 11):
        out["comm_patterns"].append({"pattern_name": sys.argv[1],
                                   "n_iters": int(sys.argv[3]),
                                   "nd_fraction": round(nd_frac, 1),
                                   "params": [
                                       {
                                           "key": "msg_size",
                                           "val": sys.argv[2]
                                       }
                                   ]})
        nd_frac += 0.1
    with open("../config/message_race_msg_size_{}_niters_{}.json".format(int(sys.argv[2]), int(sys.argv[3])), 'w+') as f:
        json.dump(out, f, indent=4)


elif sys.argv[1] == "mini_mcb":
    nd_frac = 0.0
    for i in range(0, 11):
        out["comm_patterns"].append({"pattern_name": sys.argv[1],
                                   "n_iters": 1,
                                   "nd_fraction": round(nd_frac, 1),
                                   "params": [
                                       {
                                           "key": "n_sub_iters",
                                           "val": "10"
                                       },
                                       {
                                           "key": "n_grid_steps",
                                           "val": "4"
                                       },
                                       {
                                           "key": "n_reduction_steps",
                                           "val": "4"
                                       },
                                       {
                                           "key": "interleave_nd_iters",
                                           "val": sys.argv[2]
                                       }
                                   ]})
        nd_frac += 0.1
    with open("mini_mcb_{}.json".format(("interleaved" if (int(sys.argv[2]) == 1) else "non_interleaved")), 'w+') as f:
        json.dump(out, f, indent=4)


elif sys.argv[1] == "unstructured_mesh":
    nd_frac = 0.0
    for i in range(0, 11):
        out["comm_patterns"].append({"pattern_name": sys.argv[1],
                                   "n_iters": 1,
                                   "nd_fraction": round(nd_frac, 1),
                                   "params": [
                                       {
                                           "key": "nd_fraction_neighbors",
                                           "val": sys.argv[2]
                                       },
                                       {
                                           "key": "n_procs_x",
                                           "val": sys.argv[3]
                                       },
                                       {
                                           "key": "n_procs_y",
                                           "val": sys.argv[4]
                                       },
                                       {
                                           "key": "n_procs_z",
                                           "val": sys.argv[5]
                                       },
                                       {
                                           "key": "min_deg",
                                           "val": "10"
                                       },
                                       {
                                           "key": "max_deg",
                                           "val": "10"
                                       },
                                       {
                                           "key": "max_dist",
                                           "val": "4"
                                       },
                                       {
                                           "key": "msg_size",
                                           "val": sys.argv[6]
                                       }
                                   ]})
        nd_frac += 0.1
    with open("unstructured_mesh_{}x{}x{}_nd_neighbor_fraction_{}_msg_size_{}.json".format(sys.argv[3], sys.argv[4], sys.argv[5], sys.argv[2], sys.argv[6]), 'w+') as f:
        json.dump(out, f, indent=4)

