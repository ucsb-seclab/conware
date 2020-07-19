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


def add_keys(stats):
    keys = ['0x400e0630', '0x400c0104', '0x400c0120', '0x400e0800', '0x400e0ea0', '0x400e0804', '0x400e0638',
            '0x400e1470', '0x400e0808', '0x400e0920', '0x400e1a54', '0x400e081c', '0x400e1054', '0x400e1064',
            '0x400e061c', '0x400e0e04', '0x400e1010', '0x400e1260', '0x400e1070', '0x400e0820', '0x400e0e64',
            '0x400e1030', '0x400c0014', '0x400e0e60', '0x400e1034', '0x400e0e44', '0x400c0114', '0x400e10a0',
            '0x400ac800', '0x400e0620', '0x400e1444', '0x400e1460', '0x400e0600', '0x400e0628', '0x400e080c',
            '0x400e0700', '0x400ac018', '0x400e12a0', '0x400e0c00', '0x400e0610', '0x400e1404', '0x400e1044',
            '0x400e14a0', '0x400e0a00', '0x400e0e70', '0x400c0010', '0x400e1060', '0x400e1004', '0x400c0004',
            '0x400e1000', '0x400c0000', '0x400ac000', '0x400c0028']
    for k in keys:
        if k not in stats['writes']:
            stats['writes'][k] = 0
        if k not in stats['reads']:
            stats['reads'][k] = 0


if __name__ == "__main__":

    # Get user input
    parser = argparse.ArgumentParser()
    parser.add_argument("recording_filename", default=None,
                        help="Filename to aggregate MMIO access in")
    # parser.add_argument("emulated_filename", default=None,
    #                     help="Filename to aggregate MMIO access in")
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
    # stats_emulated = get_log_stats(args.emulated_filename)

    # Even out addresses
    # for v in stats_recording['writes']:
    #     if v not in stats_recording['reads']:
    #         stats_recording['reads'][v] = 0
    # for v in stats_recording['reads']:
    #     if v not in stats_recording['writes']:
    #         stats_recording['writes'][v] = 0

    even_keys(stats_recording['writes'], stats_recording['reads'])
    add_keys(stats_recording)
    # even_keys(stats_emulated['writes'], stats_emulated['reads'])
    # even_keys(stats_emulated['writes'], stats_recording['reads'])
    # even_keys(stats_recording['writes'], stats_emulated['reads'])
    pprint.pprint(stats_recording)

    # Width of bar
    width = .5

    # Writes: real
    od_writes = collections.OrderedDict(sorted(stats_recording['writes'].items()))
    indices = np.arange(len(od_writes.keys()))
    plt.bar(indices - width / 2,
            [100 * float(x) / stats_recording['total_writes'] for x in od_writes.values()],
            width,
            label="Recorded Writes")

    # Reads: real
    od_reads = collections.OrderedDict(sorted(stats_recording['reads'].items()))
    plt.bar(indices + width / 2,
            [100 * float(x) / stats_recording['total_reads'] for x in od_reads.values()],
            width,
            # bottom=[100*float(x) / stats_recording['total_writes'] for x in od_writes.values()],
            label="Recorded Reads"
            )

    plt.xticks(indices, [str(x).upper() for x in od_writes.keys()], rotation=90, fontsize=5, fontname="Courier New")
    # plt.xticks(od.keys(), rotation=90)
    plt.yscale("log")
    plt.xlim([indices[0] - width, indices[-1] + width])
    plt.xlabel("Peripheral address accessed")
    plt.ylabel("Percentage of accesses (%)")
    plt.legend()
    # plt.show()
    plt.gcf().subplots_adjust(bottom=0.2)
    plt.savefig(args.filename)

    sys.exit(0)


    def plot_data(axs, stats):
        # Writes: emulated
        od_writes = collections.OrderedDict(sorted(stats['writes'].items()))
        indices = np.arange(len(od_writes.keys()))
        print sum(od_writes.values())
        print stats['total_writes']
        print [100 * float(x) / stats['total_writes'] for x in od_writes.values()]
        axs.bar(indices - width / 2,
                [100 * float(x) / stats['total_writes'] for x in od_writes.values()],
                width,
                label="Emulated Writes")
        # Reads: emulated
        od_reads = collections.OrderedDict(sorted(stats['reads'].items()))
        axs.bar(indices + width,
                [100 * float(x) / stats['total_reads'] for x in od_reads.values()],
                width,
                # bottom=[100*float(x) / stats_emulated['total_writes'] for x in od_writes.values()],
                label="Emulated Reads")
        axs.set_xticks(indices, od_writes.keys())


    from matplotlib import gridspec

    fig = plt.figure()
    gs = gridspec.GridSpec(1, 2)
    axs0 = plt.subplot(gs[0])
    axs1 = plt.subplot(gs[1], sharey=axs0)
    # axs = gs.subplots(sharex=True, sharey=True)

    plt.yscale("log")
    plt.xlabel("Peripheral address accessed")
    plt.ylabel("Percentage of accesses")
    plot_data(axs0, stats_recording)
    plot_data(axs1, stats_recording)
    plt.setp(axs1.get_yticklabels(), visible=False)
    plt.subplots_adjust(wspace=.0)
    # plt.xticks(od.keys(), rotation=90)
    plt.legend()

    plt.show()
    sys.exit(0)

    # Writes: emulated
    od_writes = collections.OrderedDict(sorted(stats_emulated['writes'].items()))
    indices = np.arange(len(od_writes.keys()))
    print sum(od_writes.values())
    print stats_emulated['total_writes']
    print [100 * float(x) / stats_emulated['total_writes'] for x in od_writes.values()]
    plt.bar(indices - width / 2,
            [100 * float(x) / stats_emulated['total_writes'] for x in od_writes.values()],
            width,
            label="Emulated Writes")

    # Reads: emulated
    od_reads = collections.OrderedDict(sorted(stats_emulated['reads'].items()))
    plt.bar(indices + width,
            [100 * float(x) / stats_emulated['total_reads'] for x in od_reads.values()],
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
