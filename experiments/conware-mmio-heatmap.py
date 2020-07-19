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

from conware.utils import get_log_stats, get_log_heatmap

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
    # parser.add_argument("emulated_filename", default=None,
    #                     help="Filename to aggregate MMIO access in")
    # parser.add_argument("filename", default="log_compare.pdf",
    #                     help="Filename to save the plot as")
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
    reads, writes = get_log_heatmap(args.recording_filename)

    def get_2d_array(nested_dict):
        # get the max y axis
        max_y = set()
        for addr in nested_dict:
            max_y |= set(nested_dict[addr].keys())

        rtn_array = []
        for val in sorted(max_y):
            row = []
            for addr in nested_dict:
                if val in nested_dict[addr]:
                    row.append(nested_dict[addr][val])
                else:
                    row.append(0)
            rtn_array.append(row)
        return rtn_array

    read_array = get_2d_array(reads)
    write_array = get_2d_array(writes)
    plt.imshow(read_array )
    plt.show()
    plt.imshow(write_array, cmap='hot', interpolation='nearest')
    plt.show()
    sys.exit(0)


    import numpy as np
    import matplotlib
    import matplotlib.pyplot as plt

    # sphinx_gallery_thumbnail_number = 2

    vegetables = ["cucumber", "tomato", "lettuce", "asparagus",
                  "potato", "wheat", "barley"]
    farmers = ["Farmer Joe", "Upland Bros.", "Smith Gardening",
               "Agrifun", "Organiculture", "BioGoods Ltd.", "Cornylee Corp."]

    harvest = np.array([[0.8, 2.4, 2.5, 3.9, 0.0, 4.0, 0.0],
                        [2.4, 0.0, 4.0, 1.0, 2.7, 0.0, 0.0],
                        [1.1, 2.4, 0.8, 4.3, 1.9, 4.4, 0.0],
                        [0.6, 0.0, 0.3, 0.0, 3.1, 0.0, 0.0],
                        [0.7, 1.7, 0.6, 2.6, 2.2, 6.2, 0.0],
                        [1.3, 1.2, 0.0, 0.0, 0.0, 3.2, 5.1],
                        [0.1, 2.0, 0.0, 1.4, 0.0, 1.9, 6.3]])

    fig, ax = plt.subplots()
    im = ax.imshow(harvest)

    # We want to show all ticks...
    ax.set_xticks(np.arange(len(farmers)))
    ax.set_yticks(np.arange(len(vegetables)))
    # ... and label them with the respective list entries
    ax.set_xticklabels(farmers)
    ax.set_yticklabels(vegetables)

    # Rotate the tick labels and set their alignment.
    plt.setp(ax.get_xticklabels(), rotation=45, ha="right",
             rotation_mode="anchor")

    # Loop over data dimensions and create text annotations.
    for i in range(len(vegetables)):
        for j in range(len(farmers)):
            text = ax.text(j, i, harvest[i, j],
                           ha="center", va="center", color="w")

    ax.set_title("Harvest of local farmers (in tons/year)")
    fig.tight_layout()
    plt.show()
    #
    # plt.xticks(indices, od_writes.keys(), rotation=90)
    # # plt.xticks(od.keys(), rotation=90)
    # plt.yscale("log")
    # plt.xlabel("Peripheral address accessed")
    # plt.ylabel("Percentage of accesses")
    # plt.legend()
    #
    # # fig, axs = plt.subplots(1, 2, sharey=True, tight_layout=True)
    # #
    # # # We can set the number of bins with the `bins` kwarg
    # # axs[0].hist(x, bins=n_bins)
    # # axs[1].hist(y, bins=n_bins)
    #
    # plt.show()
    # plt.savefig(args.filename)
