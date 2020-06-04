#!/usr/bin/env python

import argparse
import collections
import csv
import fnmatch
import logging
import os
import pprint
import sys
import matplotlib.pyplot as plt
import numpy as np
from matplotlib import colors
from matplotlib.ticker import PercentFormatter

from conware.utils import get_log_stats

logger = logging.getLogger(__name__)

def even_keys(d1, d2):
    # Even out addresses
    for v in d1:
        if v not in d2:
            d2[v] = 0
    for v in d2:
        if v not in d1:
            d1[v] = 0

if __name__ == "__main__":

    # Get user input
    parser = argparse.ArgumentParser()
    parser.add_argument("recording_filename", default=None,
                        help="Filename to aggregate MMIO access in")
    parser.add_argument("emulated_filename", default=None,
                        help="Filename to aggregate MMIO access in")
    parser.add_argument("filename", default="log_compare.pdf",
                        help="Filename to save the plot as")
    parser.add_argument("--debug", "-d", default=False, action='store_true',
                        help="Enable debug output.")
    args = parser.parse_args()

    if not os.path.exists(args.recording_filename):
        parser.print_help()
        sys.exit(0)

    # Setup Logging
    if args.debug:
        logging.basicConfig(level=logging.DEBUG)
    else:
        logging.basicConfig(level=logging.INFO)

    logger.info("Opening %s..." % args.recording_filename)
    stats_recording = get_log_stats(args.recording_filename)
    stats_emulated = get_log_stats(args.emulated_filename)

    # Even out addresses
    # for v in stats_recording['writes']:
    #     if v not in stats_recording['reads']:
    #         stats_recording['reads'][v] = 0
    # for v in stats_recording['reads']:
    #     if v not in stats_recording['writes']:
    #         stats_recording['writes'][v] = 0

    even_keys(stats_recording['writes'], stats_recording['reads'])
    even_keys(stats_emulated['writes'], stats_emulated['reads'])
    # even_keys(stats_emulated['writes'], stats_recording['reads'])
    # even_keys(stats_recording['writes'], stats_emulated['reads'])
    pprint.pprint(stats_recording)

    # Width of bar
    width = .3

    # Writes: real
    od_writes = collections.OrderedDict(sorted(stats_recording['writes'].items()))
    indices = np.arange(len(od_writes.keys()))
    plt.bar(indices - width,
            [100*float(x) / stats_recording['total_writes'] for x in od_writes.values()],
            width,
            label="Recorded Writes")

    # Reads: real
    od_reads = collections.OrderedDict(sorted(stats_recording['reads'].items()))
    plt.bar(indices + width / 2,
            [100*float(x) / stats_recording['total_reads'] for x in od_reads.values()],
            width,
            # bottom=[100*float(x) / stats_recording['total_writes'] for x in od_writes.values()],
            label="Recorded Reads"
            )


    # Writes: emulated
    od_writes = collections.OrderedDict(sorted(stats_emulated['writes'].items()))
    indices = np.arange(len(od_writes.keys()))
    plt.bar(indices - width/2,
            [100*float(x) / stats_emulated['total_writes'] for x in od_writes.values()],
            width,
            label="Emulated Writes")

    # Reads: emulated
    od_reads = collections.OrderedDict(sorted(stats_emulated['reads'].items()))
    plt.bar(indices + width,
            [100*float(x) / stats_emulated['total_reads'] for x in od_reads.values()],
            width,
            # bottom=[100*float(x) / stats_emulated['total_writes'] for x in od_writes.values()],
            label="Emulated Reads")

    # # Writes: emulated
    # od_writes = collections.OrderedDict(sorted(stats_emulated['writes'].items()))
    # indicies = np.arange(len(od_writes.keys()))
    # plt.bar(indicies + width / 2, od_writes.values(), width, color='y')
    # # Reads: emulated
    # od_reads = collections.OrderedDict(sorted(stats_emulated['reads'].items()))
    # plt.bar(indicies + width / 2, od_reads.values(), width, bottom=od_writes.values(), color='grey')

    plt.xticks(indices, od_writes.keys(), rotation=90)
    # plt.xticks(od.keys(), rotation=90)
    plt.yscale("log")
    plt.xlabel("Peripheral address accessed")
    plt.ylabel("Percentage of accesses")
    plt.legend()

    # fig, axs = plt.subplots(1, 2, sharey=True, tight_layout=True)
    #
    # # We can set the number of bins with the `bins` kwarg
    # axs[0].hist(x, bins=n_bins)
    # axs[1].hist(y, bins=n_bins)

    plt.show()
    plt.savefig(args.filename)
