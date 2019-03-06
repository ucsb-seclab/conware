#!/usr/bin/python
import argparse
import sys
import subprocess
import os
import tempfile


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

    required_named = parser

    required_named.add_argument('-i', action='store', dest='src_ico_file',
                                help='Path to the source ico file.',
                                required=True)

    required_named.add_argument('-b', action='store', dest='target_build_dir',
                                help='Path to the build directory.',
                                required=True)

    required_named.add_argument('-r', action='store', dest='original_repo_dir',
                                help='Path to the original repo directory.',
                                required=True)

    return parser


def run_default_arduino_build(build_dir, repo_dir, ico_file_path, build_output_file):
    to_run_command_template = "$3/runtime/arduino-1.8.8/arduino-builder -debug-level 5 -verbose -compile " \
                     "-logger=machine -hardware $3/runtime/arduino-1.8.8/hardware " \
                     "-hardware $3/runtime/arduino-1.8.8/portable/packages " \
                     "-tools $3/runtime/arduino-1.8.8/tools-builder " \
                     "-tools $3/runtime/arduino-1.8.8/hardware/tools/avr -tools $3/runtime/arduino-1.8.8/" \
                     "portable/packages " \
                     "-built-in-libraries $3/runtime/arduino-1.8.8/libraries " \
                     "-libraries $3/runtime/arduino-1.8.8/portable/sketchbook/libraries " \
                     "-fqbn=arduino:sam:arduino_due_x_dbg -ide-version=10808 " \
                     "-build-path $1 -warnings=null " \
                     "-prefs=build.path=$1 -prefs=build.warn_data_percentage=75 " \
                     "-prefs=runtime.tools.bossac.path=$3/runtime/arduino-1.8.8/portable/packages/arduino/tools/" \
                     "bossac/1.6.1-arduino " \
                     "-prefs=runtime.tools.bossac-1.6.1-arduino.path=$3/runtime/arduino-1.8.8/portable/packages/" \
                     "arduino/tools/bossac/1.6.1-arduino " \
                     "-prefs=runtime.tools.arm-none-eabi-gcc.path=$3/runtime/arduino-1.8.8/portable/packages/arduino/" \
                     "tools/arm-none-eabi-gcc/4.8.3-2014q1 " \
                     "-prefs=runtime.tools.arm-none-eabi-gcc-4.8.3-2014q1.path=$3/runtime/arduino-1.8.8/portable/" \
                     "packages/arduino/tools/arm-none-eabi-gcc/4.8.3-2014q1 $2 > " + build_output_file + " 2>&1"

    to_run_command = to_run_command_template.replace("$3", repo_dir)
    to_run_command = to_run_command.replace("$1", build_dir)
    to_run_command = to_run_command.replace("$2", ico_file_path)

    log_info("Running original arduino build and writing output to:", build_output_file)
    if not os.system(to_run_command):
        log_success("Succesfully built arduino build.")
    else:
        log_error("Error occurred while trying to run arduino build.")


def parse_arduino_builder_out(arduino_builder_output, output_compile_json):
    target_script = os.path.join(os.path.dirname(__file__), "util_scripts/parse_arduino_builder_output.py")
    if os.path.exists(target_script):
        to_run_cmd = "python " + target_script + " -i " + arduino_builder_output + " -o " + output_compile_json
        log_info("Running arduino builder output parser.")
        os.system(to_run_cmd)
        log_success("Finished parsing builder output to json file:", output_compile_json)
        return True
    else:
        return False


def get_bin_path(bin_name):
    out_p = subprocess.check_output('which ' + bin_name, shell=True)
    return out_p.strip()


def perform_llvm_transformation(llvm_bc_out, original_build_dir, compile_json_out, clang_path, opt_path, so_path):
    target_script = os.path.join(os.path.dirname(__file__), "llvm_build/arduino_llvm_build.py")
    if os.path.exists(target_script):
        to_run_cmd = "python " + target_script + " -l " + llvm_bc_out + " -b " + original_build_dir + \
                     " -m " + compile_json_out + " -clangp " + clang_path + \
                     " -instrument -optp " + opt_path + " -sopath " + so_path
        log_info("Running llvm transformations.")
        os.system(to_run_cmd)
        log_success("Finished running llvm transformations.")
        return True
    else:
        return False


def main():
    arg_parser = setup_args()
    parsed_args = arg_parser.parse_args()
    path_to_ico_file = parsed_args.src_ico_file
    original_repo_dir = parsed_args.original_repo_dir
    target_build_dir = parsed_args.target_build_dir
    llvm_transformation_pass_so = os.path.join(os.path.dirname(__file__),
                                               "llvm_transformation_passes/build/MMIOLogger/libMMIOLogger.so")

    clang_path = get_bin_path("clang")
    opt_path = get_bin_path("opt")

    if not os.path.exists(path_to_ico_file):
        log_error("Provided ico file doesn't exist:", path_to_ico_file)
        sys.exit(-1)

    if not os.path.exists(original_repo_dir):
        log_error("Provided repo directory doesn't exist:", original_repo_dir)
        sys.exit(-1)

    if not os.path.exists(llvm_transformation_pass_so):
        log_error("LLVM Transformation so file:", llvm_transformation_pass_so, " doesn't exist.")
        sys.exit(-1)

    if not os.path.exists(clang_path):
        log_error("clang doesn't exist in system path.")
        sys.exit(-1)

    if not os.path.exists(opt_path):
        log_error("opt binary doesn't exist in system path.")
        sys.exit(-1)

    if not target_build_dir:
        log_error("No build directory provided.")
        sys.exit(-1)

    if os.path.exists(target_build_dir):
        log_warning("Cleaning up provided build directory:", target_build_dir)
        os.system("rm -rf " + target_build_dir)

    if not os.path.exists(target_build_dir):
        os.makedirs(target_build_dir)

    tmp_work_directory = tempfile.mkdtemp()
    log_info("Using Directory:", tmp_work_directory, " as temporary working directory.")
    # do original build to capture the build commands.
    original_build_output = os.path.join(tmp_work_directory, "original_arduino_build_output.txt")
    run_default_arduino_build(target_build_dir, original_repo_dir, path_to_ico_file, original_build_output)

    # convert the build commands to json
    output_compile_json = os.path.join(tmp_work_directory, "compile_commands.json")
    if not parse_arduino_builder_out(original_build_output, output_compile_json):
        sys.exit(-3)

    # generate, transform and replace object files.
    llvm_bit_code_output = os.path.join(tmp_work_directory, "llvm_bitcode_out")
    if not os.path.exists(llvm_bit_code_output):
        os.makedirs(llvm_bit_code_output)
    perform_llvm_transformation(llvm_bit_code_output, target_build_dir, output_compile_json,
                                clang_path, opt_path, llvm_transformation_pass_so)

    # run build again to use the modified object files.
    modified_build_output = os.path.join(tmp_work_directory, "modified_arduino_build_output.txt")
    run_default_arduino_build(target_build_dir, original_repo_dir, path_to_ico_file, modified_build_output)


if __name__ == "__main__":
    main()
