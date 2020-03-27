#!/bin/sh

root=$PWD

mkdir llvm_build_infra/llvm_transformation_passes/build/
cd llvm_build_infra/llvm_transformation_passes/build/
cmake ..
make || { echo 'Failed to build LLVM pass' ; exit 1; }
cd $root
echo "LLVM passes built successfully!"

cd ./runtime/arduino-1.8.8/portable/packages/arduino/hardware/sam/1.6.11/system/libsam/build_gcc
make clean
make -f Makefile.clang || { echo 'Failed to build Arduino SAM' ; exit 1; }
cd $root
echo "Arduino SAM built successfully!"

cp runtime/arduino-1.8.8/portable/packages/arduino/hardware/sam/1.6.11/variants/arduino_due_x/libsam_sam3x8e_clang_rel.a runtime/arduino-1.8.8/portable/packages/arduino/hardware/sam/1.6.11/variants/arduino_due_x/libsam_sam3x8e_gcc_rel.a

