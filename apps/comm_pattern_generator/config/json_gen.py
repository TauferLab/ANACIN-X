import json
import sys
import os

#print(os.getcwd())
out = {"comm_patterns": []}


if sys.argv[1] == "amg2013":
    nd_frac = float(sys.argv[5])
    while True:
        out["comm_patterns"].append( {"pattern_name": sys.argv[1],
                                   "n_iters": int(sys.argv[3]),
                                   "nd_fraction": round(nd_frac, 2),
                                   "params": [
                                       {
                                           "key": "msg_size",
                                           "val": sys.argv[2]
                                       }
                                   ]})
        nd_frac += float(sys.argv[6])
        if ( (nd_frac > float(sys.argv[7])) or (float(sys.argv[6]) == 0) ):
            break;
    with open("{}/amg2013_msg_size_{}_niters_{}_ndp_{}_{}_{}.json".format(sys.argv[4], int(sys.argv[2]), int(sys.argv[3]), float(sys.argv[5]), float(sys.argv[6]), float(sys.argv[7])), 'w+') as f:
        json.dump(out, f, indent=4)

elif sys.argv[1] == "naive_reduce":
    nd_frac = float(sys.argv[5])
    while True:
        out["comm_patterns"].append({"pattern_name": sys.argv[1],
                                   "n_iters": int(sys.argv[3]),
                                   "nd_fraction": round(nd_frac, 2),
                                   "params": [
                                       {
                                           "key": "msg_size",
                                           "val": sys.argv[2]
                                       }
                                   ]})
        nd_frac += float(sys.argv[6])
        if ( (nd_frac > float(sys.argv[7])) or (float(sys.argv[6]) == 0) ):
            break;
    with open("{}/message_race_msg_size_{}_niters_{}_ndp_{}_{}_{}.json".format(sys.argv[4], int(sys.argv[2]), int(sys.argv[3]), float(sys.argv[5]), float(sys.argv[6]), float(sys.argv[7])), 'w+') as f:
        json.dump(out, f, indent=4)

elif sys.argv[1] == "mini_mcb":
    print(f'Creating mini mcb json')
    # nd_frac = 0.0
    nd_frac = float(sys.argv[5])
    # for i in range(0, 11):
    while True:
        out["comm_patterns"].append({"pattern_name": sys.argv[1],
                                   "n_iters": int(sys.argv[3]),
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
                                           "val": "0"
                                       },
                                       {
                                           "key": "interleave_nd_iters",
                                           "val": sys.argv[2]
                                       }
                                   ]})
        # nd_frac += 0.1
        nd_frac += float(sys.argv[6])
        if ( (nd_frac > float(sys.argv[7])) or (float(sys.argv[6]) == 0) ):
            break;
    with open("{}/config/mini_mcb_{}_niters_{}.json".format(sys.argv[4],("interleaved" if (int(sys.argv[2]) == 1) else "non_interleaved"), int(sys.argv[3])), 'w+') as f:
        json.dump(out, f, indent=4)

elif sys.argv[1] == "unstructured_mesh":
    nd_frac = float(sys.argv[9])
    while True:
        out["comm_patterns"].append({"pattern_name": sys.argv[1],
                                     "n_iters": int(sys.argv[7]),
                                   "nd_fraction": round(nd_frac, 2),
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
        nd_frac += float(sys.argv[10])
        if (nd_frac > float(sys.argv[11])) or (float(sys.argv[10]) == 0):
            break;
    with open("{}/unstructured_mesh_{}x{}x{}_nd_neighbor_fraction_{}_msg_size_{}_niters_{}_ndp_{}_{}_{}.json".format(sys.argv[8], int(sys.argv[3]), int(sys.argv[4]), int(sys.argv[5]), sys.argv[2], int(sys.argv[6]), int(sys.argv[7]), str(sys.argv[9]), str(sys.argv[10]), str(sys.argv[11])), 'w+') as f:
        json.dump(out, f, indent=4)

