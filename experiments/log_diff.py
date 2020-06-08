import argparse

import logging
import os
import pprint

from conware.utils import get_log_diff
logger = logging.getLogger(__name__)

def print_results(results):
    for name in results:

        out_dict = ["\\texttt{%s}" % name]
        out_dict.append("%d (%.03f)" % (results[name]['conflicts'],
                                      100.0*results[name]['conflicts']/results[name]['total']))
        out_dict.append("%d (%.03f)" % (results[name]['missing_emulated'],
                                      100.0*results[name]['missing_emulated']/results[name]['total']))
        out_dict.append("%d (%.03f)" % (results[name]['missing_emulated'],
                                      100.0*results[name]['missing_emulated']/results[name]['total']))
        # out_dict.append('{:,}'.format(results[name]['total']))
        out_dict.append('{:,}'.format(results[name]['total_emulated']))
        out_dict.append('{:,}'.format(results[name]['total_recorded']))
        print(" & ".join(out_dict) + "\\\\")


if __name__ == "__main__":
    parser = argparse.ArgumentParser()

    parser.add_argument('firmware_directory', default="../firmware/custom")

    args = parser.parse_args()

    logging.basicConfig(level=logging.INFO)

    results = {}
    results_linear = {}
    for dir in os.listdir(args.firmware_directory):
        print os.path.basename(dir)
        emulated_log = os.path.join(args.firmware_directory, dir, "emulated_output.csv")
        if not os.path.exists(emulated_log):
            logger.error("%s does not exist!" % emulated_log)
            continue
        emulated_log_linear = os.path.join(args.firmware_directory, dir, "emulated_output_linear.csv")
        if not os.path.exists(emulated_log_linear):
            logger.error("%s does not exist!" % emulated_log)
            continue
        recorded_log = os.path.join(args.firmware_directory, dir, "recording.tsv")
        if not os.path.exists(recorded_log):
            logger.error("%s does not exist!" % recorded_log)
            continue
        try:
            results[os.path.basename(dir)] = get_log_diff(emulated_log, recorded_log, None)
        except:
            logger.exception("Log parsing failed")
        try:
            results_linear[os.path.basename(dir)] = get_log_diff(emulated_log_linear, recorded_log, None)
        except:
            logger.exception("Log parsing failed")


    print("Normal")
    print_results(results)
    print("Linear")
    print_results(results_linear)