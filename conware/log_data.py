import argparse
import os
import logging
import pprint

import serial
import sys

from conware.hardware import Arduino


logger = logging.getLogger(__name__)
logging.basicConfig(level=logging.DEBUG)

if __name__ == "__main__":

    parser = argparse.ArgumentParser()

    parser.add_argument('project_path', action='store',
                        help='Path to Arduino project.')

    parser.add_argument('-l', action='store', dest='location',
                        help='Programmer location in /dev (e.g., '
                             'ttyACM0)',
                        default="ttyACM0")

    args = parser.parse_args()

    if not os.path.exists(args.project_path):
        print("ERROR: Project path (%s) does not exist." % args.project_path)
        sys.exit(1)

    bin_name = os.path.basename(args.project_path.strip("/")) + ".ino.bin"
    build_dir = "build"
    binary_filename = os.path.abspath(os.path.join(args.project_path, build_dir,
                                          bin_name))
    if not os.path.exists(binary_filename):
        print("ERROR: Binary file (%s) does not exist." % binary_filename)
        sys.exit(1)

    log_filename = os.path.join(args.project_path, "recording.tsv")
    due = Arduino(args.location)
    due.upload_binary(binary_filename)
    due.log_data(log_filename)

    print "Done."
