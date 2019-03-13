#!/bin/sh
root=$PWD
./rebuild_runtime.sh || exit 1
cd llvm_build_infra
python instrument_arduino_project.py -i /home/cspensky/projects/conware/projects_custom/blink/blink.ino -b /home/cspensky/projects/conware/llvm_build_infra/build/ -r /home/cspensky/projects/conware/ || exit 1 || exit 1
cd ..

./upload_bin.sh llvm_build_infra/build/blink.ino.bin 
