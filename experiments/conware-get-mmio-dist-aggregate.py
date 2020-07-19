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

from conware.ground_truth.arduino_due import PeripheralMemoryMap
from conware.model import ConwareModel
import conware.globals as G
from conware.utils import get_log_stats

peripheral_memory_map = PeripheralMemoryMap()

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

    lock_stats = {}
    peripheral_stats = {}
    for dir in os.listdir(args.firmware_directory):
        if not os.path.isdir(os.path.join(args.firmware_directory, dir)):
            continue
        recording_file = os.path.join(args.firmware_directory, dir, 'emulated_output.csv')
        if "lock" in dir:
            if "longer" not in dir:
                continue
            print "Getting lock stats...", dir
            lock_stats = get_log_stats(recording_file)
        else:
            tmp_stats = get_log_stats(recording_file)
            for k in tmp_stats:
                if k not in peripheral_stats:
                    peripheral_stats[k] = tmp_stats[k]
                elif k == "peripherals":
                    for p in tmp_stats[k]:
                        peripheral_stats[k].add(p)
                elif 'total' in k:
                    peripheral_stats[k] += tmp_stats[k]
                else:
                    for a in tmp_stats[k]:
                        if a not in peripheral_stats[k]:
                            peripheral_stats[k][a] = tmp_stats[k][a]
                        else:
                            peripheral_stats[k][a] += tmp_stats[k][a]

    print lock_stats.keys()
    for k in lock_stats:
        if 'total' in k:
            print k, lock_stats[k]
    print peripheral_stats.keys()
    for k in peripheral_stats:
        if 'total' in k:
            print k, peripheral_stats[k]

    for i in peripheral_stats['interrupts']:
        if i not in lock_stats['interrupts']:
            print "interrupt missing!! ", i

    same_interrupt = 0
    different_interrupt = 0
    new_interrupt = 0
    for i in peripheral_stats['interrupts']:
        if i not in lock_stats['interrupts']:
            print "interrupt missing!! ", i
            different_interrupt += 1
        else:
            same_interrupt += 1

    for i in lock_stats['interrupts']:
        if i not in peripheral_stats['interrupts']:
            new_interrupt += 1

    print "missing interrupts:", different_interrupt
    print "same interrupts:", same_interrupt
    print "new interrupts:", new_interrupt

    different_address = 0
    same_address = 0
    new_address = 0
    for a in peripheral_stats['addresses']:
        if a not in lock_stats['addresses']:
            # print "Address missing! ", a
            different_address += 1
        else:
            same_address += 1

    for a in lock_stats['addresses']:
        if a not in peripheral_stats['addresses']:
            new_address += 1

    print "missing addresses:", different_address
    print "same addresses:", same_address
    print "new addresses:", new_address

    different_address_val = 0
    same_address_val = 0
    new_address_val = 0
    missed = {}
    for a in peripheral_stats['address_values']:
        if a not in lock_stats['address_values']:
            # print "Address_value missing! ", a
            periph = peripheral_memory_map.get_peripheral(int(a[0], 16), a[1])
            if periph[0] not in missed:
                missed[periph[0]] = 0
            missed[periph[0]] += 1
            different_address_val += 1
        else:
            same_address_val += 1
    for a in lock_stats['address_values']:
        if a not in peripheral_stats['address_values']:
            new_address_val += 1
    pprint.pprint(missed)
    print "missing address/val:", different_address_val
    print "same address/val:", same_address_val
    print "new address/val:", new_address_val
