import argparse
from compile_json_parser import parse_compile_json
from clang_build import build_using_clang
from log_stuff import *
import sys
import subprocess
import os


def setup_args():
    parser = argparse.ArgumentParser()

    required_named = parser

    required_named.add_argument('-l', action='store', dest='llvm_bc_out',
                                help='Destination directory where all the generated bitcode files should be stored.',
                                required=True)

    required_named.add_argument('-b', action='store', dest='original_build_base',
                                help='Build directory provided to the original arduino-builder command.',
                                required=True)

    required_named.add_argument('-m', action='store', dest='compile_json',
                                help='Path to the compile commands json file.', required=True)

    required_named.add_argument('-clangp', action='store', dest='clang_path',
                                help='Absolute path to the clang binary')

    return parser


def main():
    arg_parser = setup_args()
    parsed_args = arg_parser.parse_args()
    clang_path = parsed_args.clang_path
    if not os.path.exists(clang_path):
        log_error("clang not available in the system path:", clang_path)
        sys.exit(-1)
    # get all the compilation commands.
    compile_commands = parse_compile_json(parsed_args.compile_json)
    os.system("mkdir -p " + parsed_args.llvm_bc_out)
    # build everything.
    build_using_clang(compile_commands, parsed_args.original_build_base,
                      clang_path, parsed_args.llvm_bc_out)
    log_success("Finished generating bitcode files into the directory:", parsed_args.llvm_bc_out)


if __name__ == "__main__":
    main()