
"""
Script that converts arduino builder compilation output
to nice json output.
This json could be used to get bitcode files for the corresponding targets.
"""
import argparse
import os
import time
import sys
import json


def log_info(*args):
    log_str = "[*] "
    for curr_a in args:
        log_str = log_str + " " + str(curr_a)
    print(log_str)


def log_error(*args):
    log_str = "[!] "
    for curr_a in args:
        log_str = log_str + " " + str(curr_a)
    print(log_str)


def log_warning(*args):
    log_str = "[?] "
    for curr_a in args:
        log_str = log_str + " " + str(curr_a)
    print(log_str)


def log_success(*args):
    log_str = "[+] "
    for curr_a in args:
        log_str = log_str + " " + str(curr_a)
    print(log_str)


def setup_args():
    parser = argparse.ArgumentParser()

    parser.add_argument('-i', action='store', dest='builder_output',
                        help='Path to the arduino builder output file')

    parser.add_argument('-o', action='store', dest='compile_commands_out', default="compile_commands.json",
                        help='Path to the file where all the compilation commands need to be dumped.')

    parser.add_argument('-w', action='store', dest='used_work_dir', default=os.getcwd(),
                        help='Working directory used for running arduino builder command.')

    return parser


def usage():
    log_error("Invalid Usage.")
    log_error("Run: python ", __file__, "--help", ", to know the correct usage.")
    sys.exit(-1)


def is_known_compiler(curr_com):
    known_compilers = ['gcc', 'g++']
    for cur_c in known_compilers:
        if curr_com.endswith(cur_c):
            return True
    return False


def process_builder_output(output_file):
    known_compilers = ['gcc', 'g++']
    curr_f = open(output_file, "r")
    all_lines = map(lambda x: x.strip(), curr_f.readlines())
    curr_f.close()
    all_lines = filter(lambda x: x, all_lines)
    ret_lines = []
    for curr_l in all_lines:
        all_parts = curr_l.split()
        if len(all_parts) > 2 and is_known_compiler(all_parts[0].strip()):
            ret_lines.append(curr_l.strip())

    # filter out pre-processing commands and filter in compilation commands.
    filtered_compilation_lines = []
    for curr_l in ret_lines:
        if " -E " not in curr_l and " -c " in curr_l:
            filtered_compilation_lines.append(curr_l)

    return filtered_compilation_lines


def get_json_string(compilation_line, work_dir):
    all_parts = compilation_line.strip().split()
    compiler_name = all_parts[0]
    all_options = []
    output_files = []
    is_output = False
    input_files = []
    indx = 1
    while indx < len(all_parts):
        curr_p = all_parts[indx]
        indx += 1
        curr_p = curr_p.strip()
        if is_output:
            output_files.append(curr_p)
            is_output = False
            continue
        # workaround to handle space in the arguments
        if curr_p.startswith("\"-DUSB_MANUFACTURER") or curr_p.startswith("\"-DUSB_PRODUCT"):
            curr_p = curr_p + " " + all_parts[indx]
            indx += 1
            all_options.append(curr_p)
            continue
        if curr_p == "-o":
            is_output = True
            continue
        if curr_p.startswith("-") or not os.path.exists(curr_p):
            all_options.append(curr_p)
            continue
        input_files.append(curr_p)

    to_ret = {"compiler": compiler_name,
              "arguments": all_options,
              "directory": work_dir,
              "file": input_files,
              "output": output_files}

    return to_ret


def main():
    arg_parser = setup_args()
    parsed_args = arg_parser.parse_args()

    input_builder_out = parsed_args.builder_output
    output_json = parsed_args.compile_commands_out
    used_work_dir = parsed_args.used_work_dir

    if input_builder_out is None or not os.path.exists(input_builder_out):
        log_error("Provided input builder output file:", str(input_builder_out), "does not exist.")
        usage()

    log_info("Input builder output file:", input_builder_out)
    log_info("Work directory of arduino builder:", used_work_dir)
    log_info("Output json file:", output_json)

    log_info("Parsing the builder output file.")
    all_compilation_lines = process_builder_output(input_builder_out)
    log_info("Got", len(all_compilation_lines), "compilation commands.")

    log_info("Converting to json lines")
    all_json_lines = map(lambda x: get_json_string(x, used_work_dir), all_compilation_lines)
    log_info("Writing to output file:", output_json)
    fp = open(output_json, "w")
    fp.write(json.dumps(all_json_lines, sort_keys=True, indent=2, separators=(',', ': ')))
    fp.close()


if __name__ == "__main__":
    main()
