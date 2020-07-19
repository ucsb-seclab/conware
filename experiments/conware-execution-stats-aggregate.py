#!/usr/bin/env python

# Native
import argparse
import fnmatch
import json
import os
import pprint

import sys

from networkx.drawing.nx_agraph import to_agraph

import logging

from conware.model import ConwareModel
import conware.globals as G

logger = logging.getLogger(__name__)

if __name__ == "__main__":
    # Get user input
    parser = argparse.ArgumentParser()
    parser.add_argument('firmware_directory', default="../firmware/custom")
    parser.add_argument("--debug", "-d", default=False, action='store_true',
                        help="Enable debug output.")
    args = parser.parse_args()

    # Setup Logging
    if args.debug:
        logging.basicConfig(level=logging.DEBUG)
    else:
        logging.basicConfig(level=logging.INFO)

    stats = {}
    stat_keys = [u'missed_writes', u'missed_reads', u'interrupts', u'total_writes', u'total_reads']
    for dir in os.listdir(args.firmware_directory):
        if not os.path.isdir(os.path.join(args.firmware_directory, dir)):
            continue
        stats_file = os.path.join(args.firmware_directory, dir, 'emulate_logs', 'stats.txt')
        if not os.path.exists(stats_file):
            logger.error("Could not find stats file for %s" % dir)

        with open(stats_file, "r") as f:
            stats_json = json.loads(f.read())
            stats[dir] = stats_json

    header = ['Firmware'] + ['Writes', 'Reads', 'Interrupts', 'Long Jumps', 'Wildcards', 'BFS']
    sub_header = [u'interrupts', u'long_jump', u'bfs', u'failed', u'reads', u'wildcard', u'writes'] * len(
        set(stats.keys()) - set(stat_keys))
    # header += sub_header
    row_count = 0

    print " & ".join(["\\bf %s " % x for x in header])
    print "\\\\ \\hline"
    for dir in stats:

        row = [dir]
        for k in stat_keys:
            if k in ['missed_writes', 'missed_reads', 'interrupts']:
                continue
            row.append(stats[dir][k])

        interrupts = 0
        long_jumps = 0
        wildcards = 0
        bfs = 0
        for peripheral in stats[dir]:
            if peripheral in stat_keys:
                continue
            interrupts += len(stats[dir][peripheral]['interrupts'])
            long_jumps += stats[dir][peripheral]['long_jump']
            wildcards += stats[dir][peripheral]['wildcard']
            bfs += stats[dir][peripheral]['bfs']
        #     for stat in stats[dir][peripheral]:
        #         if isinstance(stats[dir][peripheral][stat], list):
        #             row.append(len(stats[dir][peripheral][stat]))
        #         else:
        #             row.append(stats[dir][peripheral][stat])

            # row.append(stats[dir][peripheral])
        row.append(interrupts)
        row.append(long_jumps)
        row.append(wildcards)
        row.append(bfs)

        # print row
        print " & ".join(['{:,}'.format(x) if isinstance(x, int) else str(x) for x in row])
        print "\\\\ \\hline"
