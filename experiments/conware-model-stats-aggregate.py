#!/usr/bin/env python

# Native
import argparse
import fnmatch
import os
import pprint

import sys

from networkx.drawing.nx_agraph import to_agraph

import logging

from conware.model import ConwareModel
import conware.globals as G

logger = logging.getLogger(__name__)


def get_stats(model):
    total_nodes = 0
    total_edges = 0
    total_loops = 0
    stats = {}
    for peripheral in model.peripherals:
        # print peripheral.name
        stats[peripheral.name] = {
            'N': peripheral.graph.number_of_nodes(),
            'E': peripheral.graph.number_of_edges(),
            'L': peripheral.graph.number_of_selfloops()
        }
        logger.debug("Nodes: ", peripheral.graph.number_of_nodes())
        logger.debug("Edges: ", peripheral.graph.number_of_edges())
        logger.debug("Self loops: ", peripheral.graph.number_of_selfloops())

        total_edges += peripheral.graph.number_of_edges()
        total_nodes += peripheral.graph.number_of_nodes()
        total_loops += peripheral.graph.number_of_selfloops()

    logger.debug("Total nodes: ", total_nodes)
    logger.debug("Total edges: ", total_edges)
    logger.debug("Total loops: ", total_loops)
    stats['nodes'] = total_nodes
    stats['edges'] = total_edges
    stats['loops'] = total_loops
    return stats


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

    results = {}
    results_optimized = {}
    for dir in os.listdir(args.firmware_directory):
        print os.path.basename(dir)

        model_file = os.path.join(args.firmware_directory, dir, G.MODEL_FILE)
        model_file_optimized = os.path.join(args.firmware_directory, dir, G.MODEL_FILE_OPTIMIZED)

        if not os.path.exists(model_file):
            logger.error("Model file (%s) does not exist.", model_file)
            continue

        if not os.path.exists(model_file_optimized):
            logger.error("Model file (%s) does not exist.", model_file_optimized)
            continue

        logger.info("Importing model file (%s)..." % model_file)
        model = ConwareModel(filename=model_file)
        results[os.path.basename(dir)] = get_stats(model)
        logger.info("Importing model file (%s)..." % model_file_optimized)
        model = ConwareModel(filename=model_file_optimized)
        results_optimized[os.path.basename(dir)] = get_stats(model)

    pprint.pprint(results)
    pprint.pprint(results_optimized)

    headers = ['']
    header_labels = []
    max_periperals = []
    for r in results:
        if len(results[r].keys()) > len(max_periperals):
            max_periperals = list(results[r].keys())
    for r in results_optimized:
        if len(results_optimized[r].keys()) > len(max_periperals):
            max_periperals = list(results_optimized[r].keys())

    for x in max_periperals:
        if x not in ['nodes', 'loops', 'edges']:
            header_labels.append(x)
    headers += ["\\multicolumn{3}{c|}{\\bf %s}" % x for x in header_labels]

    print " & ".join(headers) + "& \\multicolumn{3}{c|}{\\bf Total} \\\\ \\hline"
    row_count = 0
    for sample in results:
        row = [sample]
        row_optimized = ["%s$_G$" % sample]
        if row_count == 0:
            print "\\bf Firmware &",
        for periph in max_periperals:
            # Normal
            if periph not in results[sample]:
                if row_count == 0:
                    print " e & l & n &"
                row.append('-')
                row.append('-')
                row.append('-')
                continue
            if isinstance(results[sample][periph], dict):
                for nel in results[sample][periph]:
                    if row_count == 0:
                        print nel, " & ",
                    row.append(results[sample][periph][nel])

        for periph in max_periperals:
            # Optimized
            if periph not in results_optimized[sample]:
                row_optimized.append('-')
                row_optimized.append('-')
                row_optimized.append('-')
                continue
            if isinstance(results_optimized[sample][periph], dict):
                for nel in results_optimized[sample][periph]:
                    row_optimized.append(results_optimized[sample][periph][nel])

        if row_count == 0:
            print "e & l & n  \\\\ \\hline"
        # Linear
        row.append(results[sample]['edges'])
        row.append(results[sample]['loops'])
        row.append(results[sample]['nodes'])
        print " & ".join(['{:,}'.format(x) if isinstance(x, int) else str(x) for x in row]) + "\\\\ "

        # Optimized
        row_optimized.append(results_optimized[sample]['edges'])
        row_optimized.append(results_optimized[sample]['loops'])
        row_optimized.append(results_optimized[sample]['nodes'])
        print " & ".join(['{:,}'.format(x) if isinstance(x, int) else str(x) for x in row_optimized]) + "\\\\ "
        print "\\hline"
        row_count += 1
