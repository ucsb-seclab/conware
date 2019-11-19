#!/usr/bin/env bash

if [ "$#" -ne 1 ]; then
    echo "Usage $0 <path to Arduino project>"
    exit 1
fi
# Absolute path to this script. /home/user/bin/foo.sh
SCRIPT=$(readlink -f $0)
# Absolute path this script is in. /home/user/bin
SCRIPTPATH=`dirname $SCRIPT`
INO_PATH=`realpath $1`
INO_NAME=`basename $1`
INO_FILE="$INO_PATH/$INO_NAME.ino"
BUILD_PATH="$INO_PATH/build"
tmpbuild="/tmp/conware_build"
echo "$tmpbuild $BUILD_PATH"
echo "Instrumeting $INFO_FILE and storing output in $BUILD_PATH..."
bash -c "python llvm_build_infra/instrument_arduino_project.py -r $SCRIPTPATH -i $INO_FILE -b $tmpbuild"
mkdir -p $BUILD_PATH
sudo cp -a $tmpbuild/* $BUILD_PATH
rm -rf $tmpbuild
