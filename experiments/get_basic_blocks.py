from __future__ import print_function

import idaapi
import idautils
import idc

from collections import deque


def main(addr):
    # for fva in idautils.Functions():
    print_basic_blocks_dfs_bfs(addr)


def print_basic_blocks_dfs_bfs(fva):
    function = idaapi.get_func(fva)
    flowchart = idaapi.FlowChart(function, None, 0x4)
    print("Function starting at 0x%x consists of %d basic blocks" % (function.startEA, flowchart.size))

    start_bb = get_start_bb(function, flowchart)
    print("Traversing flowchart using recursive depth-first search")
    found_bbs = []
    while len(found_bbs) != flowchart.size:
        found_bbs = dfs_bbs(start_bb, found_bbs)
    for bb in found_bbs:
        print("%s" % format_bb(flowchart[bb]))

    print("Traversing flowcahart using breadth-first search")
    for bb in bfs_bbs(start_bb):
        print("%s" % format_bb(flowchart[bb]))


def get_start_bb(function, flowchart):
    for bb in flowchart:
        if bb.startEA == function.startEA:
            return bb


def dfs_bbs(start_bb, found_bbs):
    found_bbs.append(start_bb.id)
    for w in start_bb.succs():
        if w.id not in found_bbs:
            dfs_bbs(w, found_bbs)
    return found_bbs


def bfs_bbs(start_bb):
    q = deque([start_bb])
    found_bbs = []
    while len(q) > 0:
        current_bb = q.popleft()
        if current_bb.id not in found_bbs:
            found_bbs.append(current_bb.id)
            for w in current_bb.succs():
                q.append(w)
    return found_bbs


def format_bb(bb):
    bbtype = {0: "fcb_normal", 1: "fcb_indjump", 2: "fcb_ret", 3: "fcb_cndret",
              4: "fcb_noret", 5: "fcb_enoret", 6: "fcb_extern", 7: "fcb_error"}
    return("ID: %d, Start: 0x%x, End: 0x%x, Last instruction: 0x%x, Size: %d, "
           "Type: %s" % (bb.id, bb.startEA, bb.endEA, idc.PrevHead(bb.endEA),
                         (bb.endEA - bb.startEA), bbtype[bb.type]))