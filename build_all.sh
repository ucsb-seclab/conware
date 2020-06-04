#!/bin/bash

# First build the uninstrumented versions
echo "Building uninstrumented Arduino runtime..."
pushd ./runtime/arduino-1.8.8/portable/packages/arduino/hardware/sam/1.6.11/system/libsam/build_gcc > /dev/null
make clean > /dev/null 2>&1  || ( echo "Failed to build uninstrumented runtime."; exit 1 )
make > /dev/null 2>&1  || ( echo "Failed to build uninstrumented runtime."; exit 1 )
popd > /dev/null

for dir in firmware/custom/*
do
    dir=${dir%*/}      # remove the trailing "/"
    echo "Building uninstrumented $dir..."
    pushd $dir >/dev/null
    # Build our project
    arduino --pref build.path=./build_uninstrumented --verify *.ino >/dev/null 2>&1 || ( echo "Failed to build uninstrumented $dir"; exit 1 )
    popd > /dev/null
done

## Now, build the instrumented versions
echo "Building instrumented version of Arduion runtime..."
./rebuild_runtime.sh

for dir in firmware/custom/*
do
    dir=${dir%*/}      # remove the trailing "/"
    echo "Building instrumented version of $dir..."    # print everything after the final "/"
    # Build our project
    ./instrument_project.sh $dir
done
