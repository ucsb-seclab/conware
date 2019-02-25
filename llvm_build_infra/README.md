# Arduclang
Setup to get bitcode file of the source files used during the compilation of the `.ino` file.

## Setup
We need LLVM to be present on the system.

### Installing LLVM
> Build LLVM and Clang (if you have already done both, just skip it)

1) Download [LLVM-7.0.1](http://releases.llvm.org/7.0.1/llvm-7.0.1.src.tar.xz), [clang-7.0.1](http://releases.llvm.org/7.0.1/cfe-7.0.1.src.tar.xz)

2) Unzip the LLVM and Clang source files
```
tar xf llvm-7.0.1.src.tar.xz
tar xf cfe-7.0.1.src.tar.xz
mv cfe-7.0.1.src llvm-7.0.1.src/tools/clang
```

3) Create your target build folder and make
```
mkdir llvm-7.0.1.obj
cd llvm-7.0.1.obj
cmake -DCMAKE_BUILD_TYPE=Debug ../llvm-7.0.1.src (or add "-DCMAKE_BUILD_TYPE:STRING=Release" for releae version)
make -j8  
```

4) Add paths for LLVM and Clang
```
export LLVM_SRC=your_path_to_llvm-7.0.1.src
export LLVM_OBJ=your_path_to_llvm-7.0.1.obj
export LLVM_DIR=your_path_to_llvm-7.0.1.obj
export PATH=$LLVM_DIR/bin:$PATH
```

## Generating the build commands
First, you need to get the build commands from the arduino system. The way to get it would be to ask the `arduino-builder` dump the compilation commands.

Lets assume you are building an `.ico` file like this:
```
./runtime/arduino-1.8.8/arduino --pref build.path=./build --verify projects_custom/blink/blink.ino
```
Lets assume that you cloned this project in the directory:
`/home/machiry/Data/mounts/bigdrive/projects/conware`.

Then, you should run the following command to get the build commands for the above project:
```
./capture_arduino_build.sh ./build ../projects_custom/blink/blink.ino /home/machiry/Data/mounts/bigdrive/projects/conware

[*] Cleaning up build directory:./build
[?] Are you sure? All contents will be deleted, if not, Ctrl + c.y
[+] Writing all build commands to: all_arduino_build_cmds.txt
[+] Running arduino-builder.
[+] Done. All the build commands are written to: all_arduino_build_cmds.txt
```

## Generate `compile_commands.json` file
Now, we process the captured build commands and process them to emit nice beautified json file with only the compilation commands
```
cd util_scripts
usage: parse_arduino_builder_output.py [-h] [-i BUILDER_OUTPUT]
                                       [-o COMPILE_COMMANDS_OUT]

optional arguments:
  -h, --help            show this help message and exit
  -i BUILDER_OUTPUT     Path to the arduino builder output file
  -o COMPILE_COMMANDS_OUT
                        Path to the file where all the compilation commands
                        need to be dumped.
```
For the above case:
```
python parse_arduino_builder_output.py -i ../all_arduino_build_cmds.txt -o compile_commands.json
[*]  Input builder output file: ../all_arduino_build_cmds.txt
[*]  Work directory of arduino builder: /home/machiry/Data/mounts/bigdrive/projects/conware/llvm_build_infra/util_scripts
[*]  Output json file: compile_commands.json
[*]  Parsing the builder output file.
[*]  Got 31 compilation commands.
[*]  Converting to json lines
[*]  Writing to output file: compile_commands.json
```

## Generating the bitcode files
Now, from the `compile_commands.json` file and `clang`, we will generate the bitcode files.
```
cd llvm_build
python arduino_llvm_build.py -h
usage: arduino_llvm_build.py [-h] -l LLVM_BC_OUT -b ORIGINAL_BUILD_BASE -m
                             COMPILE_JSON [-clangp CLANG_PATH]

optional arguments:
  -h, --help            show this help message and exit
  -l LLVM_BC_OUT        Destination directory where all the generated bitcode
                        files should be stored.
  -b ORIGINAL_BUILD_BASE
                        Build directory provided to the original arduino-builder
                        command.
  -m COMPILE_JSON       Path to the compile commands json file.
  -clangp CLANG_PATH    Absolute path to the clang binary

```
For our example:
```
python arduino_llvm_build.py -l /home/machiry/Desktop/checking -b /home/machiry/Data/mounts/bigdrive/projects/conware/build -m /home/machiry/Data/mounts/bigdrive/projects/conware/llvm_build_infra/util_scripts/compile_commands.json -clangp /home/machiry/Data/mounts/bigdrive/tools/llvm-7.0.1.obj/bin/clang

[*]  Writing all compilation commands in json format to /home/machiry/Desktop/checking/clang_build.json
[*]  Writing all compilation commands in human usable form to /home/machiry/Desktop/checking/clang_build.txt
[*]  Got: 31 commands to process. Running in multiprocessor mode.
[*]  Finished running compilation commands in multiprocessor mode.
[+]  Finished generating bitcode files into the directory: /home/machiry/Desktop/checking
```
There you go!
All the bitcode files will be present in the folder: `/home/machiry/Desktop/checking`. Now we can modify each bitcode.

Also, this script writes all the commands to `/home/machiry/Desktop/checking/clang_build.json`:
For each object file (`orig_obj_file`), this file contains commands to convert bitcode file to object file (`from_llvm_bc_to_obj`), directly generate object file from clang (`to_llvm_obj`), generate bitcode file (`to_llvm_bc`).


## Converting the bitcode file to object file
For a given bitcode file, you can refer the above json to get the command (`from_llvm_bc_to_obj`) to convert the bitcode file into object file.

Example, snippet from `clang_build.txt`:
```
/home/machiry/Data/mounts/bigdrive/tools/llvm-7.0.1.obj/bin/clang -target armv7-a -g -O0 -Wno-return-type -w -c -g -std=gnu++11 -ffunction-sections -fdata-sections -nostdlib -fno-threadsafe-statics --param max-inline-insns-single=500 -fno-rtti -fno-exceptions -Dprintf=iprintf -MMD -mcpu=cortex-m3 -mthumb -DF_CPU=84000000L -DARDUINO=10808 -DARDUINO_SAM_DUE -DARDUINO_ARCH_SAM -D__SAM3X8E__ -mthumb -DUSB_VID=0x2341 -DUSB_PID=0x003e -DUSBCON "-DUSB_MANUFACTURER=\"Arduino LLC\"" "-DUSB_PRODUCT=\"Arduino Due\"" -I/home/machiry/Data/mounts/bigdrive/projects/conware/runtime/arduino-1.8.8/portable/packages/arduino/hardware/sam/1.6.11/system/libsam -I/home/machiry/Data/mounts/bigdrive/projects/conware/runtime/arduino-1.8.8/portable/packages/arduino/hardware/sam/1.6.11/system/CMSIS/CMSIS/Include/ -I/home/machiry/Data/mounts/bigdrive/projects/conware/runtime/arduino-1.8.8/portable/packages/arduino/hardware/sam/1.6.11/system/CMSIS/Device/ATMEL/ -I/home/machiry/Data/mounts/bigdrive/projects/conware/runtime/arduino-1.8.8/portable/packages/arduino/hardware/sam/1.6.11/cores/arduino -I/home/machiry/Data/mounts/bigdrive/projects/conware/runtime/arduino-1.8.8/portable/packages/arduino/hardware/sam/1.6.11/variants/arduino_due_x -c /home/machiry/Desktop/crap/checking2/core/USARTClass.cpp.o.bc -o /home/machiry/Desktop/crap/checking2/core/USARTClass.cpp.o.bc_frombc.obj
```

Lets check the files:
```
# input file:
$ file /home/machiry/Desktop/crap/checking2/core/USARTClass.cpp.o.bc
/home/machiry/Desktop/crap/checking2/core/USARTClass.cpp.o.bc: LLVM IR bitcode
# output file:
$ file /home/machiry/Desktop/crap/checking2/core/USARTClass.cpp.o.bc
/home/machiry/Desktop/crap/checking2/core/USARTClass.cpp.o.bc: LLVM IR bitcode
```
TADA!!!

See, how the input is the bitcode file (`.bc`) and the output is the object file (`.obj`).

__Note: The commands generated are machine friendly, however, if you want human runnable commands you can use `clang_build.txt`.__

