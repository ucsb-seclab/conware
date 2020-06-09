#!/usr/bin/env python

# Native
import argparse
import fnmatch
import os

import sys

from networkx.drawing.nx_agraph import to_agraph

import logging

from conware.model import PretenderModel
from conware.models.pattern import PatternModel

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


    addr = 0x400e0814
    ready_bit = 0b10

    # model_file = os.path.join(args.recording_dir, G.MODEL_FILE_OPTIMIZED)
    if not os.path.exists(args.model_filename):
        logger.error("Model file (%s) does not exist.", args.model_filename)
        parser.print_help()
        sys.exit(0)

    logger.info("Importing model file (%s)..." % args.model_filename)
    model = PretenderModel(filename=args.model_filename)

    # Modify every state make it ready
    for peripheral in model.peripherals:
        if peripheral.name == "UART":
            for node in peripheral.graph.nodes:
                state = peripheral._get_state(node)
                if addr in state.model_per_address:
                    print state.model_per_address[addr]
                    if isinstance(state.model_per_address[addr], PatternModel):
                        read_patterns = state.model_per_address[addr].read_patterns
                        for val in state.model_per_address[addr].read_patterns:
                            cur_vals = state.model_per_address[addr].read_patterns[val]
                            new_vals = []
                            for val_list in cur_vals:
                                 new_vals.append([x | ready_bit for x in val_list])
                            state.model_per_address[addr].read_patterns[val] = new_vals
    print "---"
    for peripheral in model.peripherals:
        if peripheral.name == "UART":
            for node in peripheral.graph.nodes:
                state = peripheral._get_state(node)
                if addr in state.model_per_address:
                    print state.model_per_address[addr]


    hacked_filename = os.path.splitext(args.model_filename)
    hacked_filename = hacked_filename[0] + "_hacked" + \
                      hacked_filename[1]
    logger.info("Saving hacked model to %s" % hacked_filename)

    model.save(hacked_filename)

