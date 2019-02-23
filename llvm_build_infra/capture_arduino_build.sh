#!/bin/bash
if [ "$#" -ne 3 ]; then
    echo "Usage: $0 <build_directory> <ico_file> <repo_root_dir>"
    exit 1
fi
if [ ! -f "$2" ]; then
    echo "Provided ico file: $2 doesn't exist."
    exit 2
fi

if [ ! -d "$3" ]; then
    echo "Provided repo root directory: $3 doesn't exist."
    exit 2
fi

BUILDOUTPUTFILE="all_arduino_build_cmds.txt"

echo "[*] Cleaning up build directory: $1"
read -p "[?] Are you sure? All contents will be deleted, if not, Ctrl + c." yn
rm -rf $1/*
echo "[+] Writing all build commands to: $BUILDOUTPUTFILE"
echo "[+] Running arduino-builder."

$3/runtime/arduino-1.8.8/arduino-builder -debug-level 5 -verbose -compile -logger=machine -hardware $3/runtime/arduino-1.8.8/hardware -hardware $3/runtime/arduino-1.8.8/portable/packages -tools $3/runtime/arduino-1.8.8/tools-builder -tools $3/runtime/arduino-1.8.8/hardware/tools/avr -tools $3/runtime/arduino-1.8.8/portable/packages -built-in-libraries $3/runtime/arduino-1.8.8/libraries -libraries $3/runtime/arduino-1.8.8/portable/sketchbook/libraries -fqbn=arduino:sam:arduino_due_x_dbg -ide-version=10808 -build-path $1 -warnings=null -prefs=build.path=$1 -prefs=build.warn_data_percentage=75 -prefs=runtime.tools.bossac.path=$3/runtime/arduino-1.8.8/portable/packages/arduino/tools/bossac/1.6.1-arduino -prefs=runtime.tools.bossac-1.6.1-arduino.path=$3/runtime/arduino-1.8.8/portable/packages/arduino/tools/bossac/1.6.1-arduino -prefs=runtime.tools.arm-none-eabi-gcc.path=$3/runtime/arduino-1.8.8/portable/packages/arduino/tools/arm-none-eabi-gcc/4.8.3-2014q1 -prefs=runtime.tools.arm-none-eabi-gcc-4.8.3-2014q1.path=$3/runtime/arduino-1.8.8/portable/packages/arduino/tools/arm-none-eabi-gcc/4.8.3-2014q1 $2 > $BUILDOUTPUTFILE 2>&1

echo "[+] Done. All the build commands are written to: $BUILDOUTPUTFILE"

