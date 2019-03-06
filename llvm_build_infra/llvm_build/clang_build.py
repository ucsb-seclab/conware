import os
from multiprocessing import Pool
from log_stuff import *
import json

# UTILITIES FUNCTION
# target optimization to be used for llvm
TARGET_OPTIMIZATION_FLAGS = ['-O0']
# debug flags to be used by llvm
DEBUG_INFO_FLAGS = ['-g']
ARCH_TARGET = '-target'
# ARM 32 architecture flag for LLVM
ARM_32_LLVM_ARCH = 'armv7'
# flags to disable some llvm warnings
DISABLE_WARNINGS = ['-Wno-return-type', '-w', '-fshort-enums']
# path to the clang binary
CLANG_PATH = 'clang'
EMIT_LLVM_FLAG = '-emit-llvm'


def _run_program((workdir, cmd_to_run)):
    """
        Run the given program with in the provided directory.
    :return: None
    """
    curr_dir = os.getcwd()
    os.chdir(workdir)
    os.system(cmd_to_run)
    os.chdir(curr_dir)


def _is_allowed_flag(curr_flag):
    """
        Function which checks, if a gcc flag is allowed in llvm command line.
    :param curr_flag: flag to include in llvm
    :return: True/False
    """
    # if this is a optimization flag, remove it.
    #if str(curr_flag)[:2] == "-O":
    #    return False

    return True


def _get_clang_build_str(clang_path, build_args, src_build_dir, work_dir,
                         src_file_path, output_file_path, llvm_bit_code_out):
    """
        Given a compilation command from the json, this function returns the clang based build string.
        assuming that the original was built with gcc
    :param clang_path: Path to clang.
    :param build_args: original arguments to the compiler.
    :param src_build_dir: Path to the original build directory given to arduino builder.
    :param work_dir: Directory where the original command was run.
    :param src_file_path: Path to the source file being compiled.
    :param output_file_path: Path to the original object file.
    :param llvm_bit_code_out: Folder where all the linked bitcode files should be stored.
    :return: (workdir,
              original obj file,
              command to convert into bitcode,
              command to generate object code,
              command to generate object code from bitcode)
    """

    curr_src_file = src_file_path
    modified_build_args = list()

    modified_build_args.append(clang_path)
    modified_build_args.append(EMIT_LLVM_FLAG)
    # Handle Target flags
    modified_build_args.append(ARCH_TARGET)
    modified_build_args.append(ARM_32_LLVM_ARCH)

    # handle debug flags
    for curr_d_flg in DEBUG_INFO_FLAGS:
        modified_build_args.append(curr_d_flg)
    # handle optimization flags
    for curr_op in TARGET_OPTIMIZATION_FLAGS:
        modified_build_args.append(curr_op)

    for curr_war_op in DISABLE_WARNINGS:
        modified_build_args.append(curr_war_op)

    rel_obj_file = output_file_path.split(src_build_dir)[-1]
    if rel_obj_file.startswith('/'):
        rel_obj_file = rel_obj_file[1:]
    target_out_dir = os.path.join(llvm_bit_code_out, os.path.dirname(rel_obj_file))
    if not os.path.exists(target_out_dir):
        os.makedirs(target_out_dir)
    target_bc_file = os.path.join(target_out_dir, os.path.basename(rel_obj_file) + ".bc")

    for curr_op in build_args:
        if _is_allowed_flag(curr_op):
            modified_build_args.append(curr_op)

    to_obj_from_bc_build_args = list(modified_build_args)
    to_obj_from_bc_build_args.remove(EMIT_LLVM_FLAG)

    # tell clang to compile.
    modified_build_args.append("-c")
    modified_build_args.append(curr_src_file)

    bitcode_to_obj_file_template = list(to_obj_from_bc_build_args)

    to_obj_from_bc_build_args.append("-c")
    to_obj_from_bc_build_args.append(target_bc_file)

    modified_build_args.append("-o")
    to_obj_from_bc_build_args.append("-o")
    # to convert into object file directly!?
    # just remove the emit-llvm flag.
    to_obj_file_build_args = list(modified_build_args)
    to_obj_file_build_args.remove(EMIT_LLVM_FLAG)
    to_obj_file_build_args.append(target_bc_file[:-2] + "llvm.obj")

    modified_build_args.append(target_bc_file)
    to_obj_from_bc_build_args.append(target_bc_file + "_frombc.obj")

    return work_dir, output_file_path, \
           target_bc_file, \
           ' '.join(bitcode_to_obj_file_template), \
           ' '.join(modified_build_args), \
           ' '.join(to_obj_file_build_args), \
           ' '.join(to_obj_from_bc_build_args)


def build_using_clang(compile_commands, original_build_base,
                      clang_path, llvm_bc_out, transformation_so=None, opt_path=None):
    output_llvm_sh_file = os.path.join(llvm_bc_out, 'clang_build.json')
    human_llvm_txt_file = os.path.join(llvm_bc_out, 'clang_build.txt')
    fp_out = open(output_llvm_sh_file, 'w')
    fp_human_out = open(human_llvm_txt_file, 'w')
    log_info("Writing all compilation commands in json format to", output_llvm_sh_file)
    log_info("Writing all compilation commands in human usable form to", human_llvm_txt_file)
    all_compilation_commands = []
    target_output_commands = []
    add_comma = False
    fp_human_out.write("{")
    transformation_info = {}
    for curr_compilation_command in compile_commands:
        work_dir, orig_output, target_bc_file, \
        bitcode_to_obj_file_template, target_command_bc_cmd, \
        target_obj_cmd, target_bc_to_obj_cmd = _get_clang_build_str(clang_path, curr_compilation_command.curr_args,
                                                                    original_build_base,
                                                                    curr_compilation_command.work_dir,
                                                                    curr_compilation_command.src_file,
                                                                    curr_compilation_command.output_file,
                                                                    llvm_bc_out)
        all_compilation_commands.append((work_dir, target_command_bc_cmd))
        curr_dict = {}
        curr_dict["orig_obj_file"] = orig_output
        curr_dict["to_llvm_bc"] = target_command_bc_cmd
        curr_dict["to_llvm_obj"] = target_obj_cmd
        curr_dict["from_llvm_bc_to_obj"] = target_bc_to_obj_cmd
        transformation_info[orig_output] = (target_bc_file, bitcode_to_obj_file_template)
        if add_comma:
            fp_human_out.write(':')
        fp_human_out.write("[")
        fp_human_out.write('"orig_obj_file": \"' + orig_output + '",\n')
        fp_human_out.write('"to_llvm_bc": \"' + target_command_bc_cmd + '",\n')
        fp_human_out.write('"to_llvm_obj": \"' + target_obj_cmd + '",\n')
        fp_human_out.write('"from_llvm_bc_to_obj": \"' + target_bc_to_obj_cmd + '"')
        fp_human_out.write("]")
        add_comma = True
        target_output_commands.append(curr_dict)

    fp_human_out.write("}")
    fp_human_out.close()
    fp_out.write("{")
    fp_out.write(json.dumps(target_output_commands, indent=4, sort_keys=True))
    fp_out.write("}")
    fp_out.close()

    log_info("Got:", len(all_compilation_commands), "commands to process. Running in multiprocessor mode.")
    p = Pool()
    p.map(_run_program, all_compilation_commands)
    log_info("Finished running compilation commands in multiprocessor mode.")

    if transformation_so is not None and opt_path is not None:
        log_info("Running transformation and converting it back to obj file.")
        for curr_output_obj in transformation_info.keys():
            orig_bc_file = transformation_info[curr_output_obj][0]
            if os.path.exists(orig_bc_file):
                fp = open(orig_bc_file, "r")
                if fp.read(2) == "BC":
                    transformation_bc_file = orig_bc_file + ".transform.bc"
                    transformation_command = opt_path + "  -load " + transformation_so + " -logmmio " + \
                                             orig_bc_file + " -o " + transformation_bc_file
                    os.system(transformation_command)
                    bc_to_obj_cmd = transformation_info[curr_output_obj][1] + \
                                    " -c " + orig_bc_file + \
                                    " -o " + curr_output_obj

                    os.system(bc_to_obj_cmd)
                else:
                    os.system("cp " + orig_bc_file + " " + curr_output_obj)
                fp.close()
        log_success("Finished running transformation passes.")



