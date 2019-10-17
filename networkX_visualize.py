#!/usr/bin/env python

# Native
import argparse
import fnmatch
import os

import sys

import logging

from pretender.model import PretenderModel
import pretender.globals as G
import pickle

import networkx
import matplotlib.pyplot as plt

from graphviz import Digraph

logger = logging.getLogger(__name__)


if __name__ == "__main__":
    # Default argument values
    sample = "bins/Nucleo_blink_led.bin"
    openocd_conf = '/usr/share/openocd/scripts/board/st_nucleo_l1.cfg'
    output_dir = '/tmp/myavatar'
    qemu_executable = "../../avatar-pretender/targets/build/qemu/arm-softmmu/qemu-system-arm"
    gdb_port = 1235
    qemu_port = 23454

    # Get user input
    parser = argparse.ArgumentParser()
    parser.add_argument("--recording_dir", "-r", default="recording",
                        help="Directory containing all of the log files")
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

    if not os.path.exists(args.recording_dir):
        parser.print_help()
        sys.exit(0)

    model_file = os.path.join(args.recording_dir, G.MODEL_FILE)
    if not os.path.exists(model_file):
        logger.error("Model file (%s) does not exist.", model_file)
        parser.print_help()
        sys.exit(0)

    logger.info("Importing model file (%s)..." % model_file)
    model = PretenderModel(filename=model_file)


    for peripheral in model.peripherals:

        # logger.info("Graphing %s..." % str(peripheral.name))
        # dot = Digraph(comment=str(peripheral))
        # bfs_graph(dot, peripheral.start_state)
        # dot.render('test.gv', view=True)
        #
        # peripheral.reset()



        logger.info("Graphing %s..." % str(peripheral.name))

        if peripheral.name == "UART" or False:
            networkx.draw(peripheral.graph)
            plt.show()
            print("Number of Nodes:")
            print(networkx.number_of_nodes(peripheral.graph))
            print("Number of Edges")
            print(networkx.number_of_edges(peripheral.graph))

    print model
