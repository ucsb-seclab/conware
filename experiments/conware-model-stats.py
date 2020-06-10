#!/usr/bin/env python

# Native
import argparse
import fnmatch
import os

import sys

from networkx.drawing.nx_agraph import to_agraph

import logging

from conware.model import ConwareModel

logger = logging.getLogger(__name__)

if __name__ == "__main__":
    # Get user input
    parser = argparse.ArgumentParser()
    parser.add_argument("model_filename",
                        help="Model filename")
    parser.add_argument("--debug", "-d", default=False, action='store_true',
                        help="Enable debug output.")
    args = parser.parse_args()

    # Setup Logging
    logging.basicConfig()
    l = logging.getLogger()
    if args.debug:
        l.setLevel(logging.DEBUG)
    else:
        l.setLevel(logging.INFO)

    # if not os.path.exists(args.recording_dir):
    #     parser.print_help()
    #     sys.exit(0)

    # model_file = os.path.join(args.recording_dir, G.MODEL_FILE_OPTIMIZED)
    if not os.path.exists(args.model_filename):
        logger.error("Model file (%s) does not exist.", args.model_filename)
        parser.print_help()
        sys.exit(0)

    logger.info("Importing model file (%s)..." % args.model_filename)
    model = ConwareModel(filename=args.model_filename)

    total_nodes = 0
    total_edges = 0
    total_loops = 0
    for peripheral in model.peripherals:
        print peripheral.name
        print "Nodes: ", peripheral.graph.number_of_nodes()
        print "Edges: ", peripheral.graph.number_of_edges()
        print "Self loops: ", peripheral.graph.number_of_selfloops()

        total_edges += peripheral.graph.number_of_edges()
        total_nodes += peripheral.graph.number_of_nodes()
        total_loops += peripheral.graph.number_of_selfloops()
        print

    print "Total nodes: ", total_nodes
    print "Total edges: ", total_edges
    print "Total loops: ", total_loops
