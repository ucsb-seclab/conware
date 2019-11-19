#!/bin/sh

# init sub modules
git submodule init
git submodule update --init --recursive
cd avatar2-pretender
git checkout master
git pull

# Install depedencies
pip install -e .

# Fix keystone
#cp $VIRTUAL_ENV/lib/python2.7/site-packages/keystone/* $VIRTUAL_ENV/lib/python2.7/site-packages/keystone/
cp $VIRTUAL_ENV/lib/python2.7/site-packages$VIRTUAL_ENV/lib/python2.7/site-packages/keystone/* $VIRTUAL_ENV/lib/python2.7/site-packages/keystone/
# Build qemu
pwd
cd ./targets/src/avatar-qemu/
git submodule update --init dtc
cd ../../
mkdir -p build
mkdir -p build/qemu
cd build/qemu
../../src/avatar-qemu/configure --disable-sdl --target-list=arm-softmmu
make -j

#for gdb executable
sudo apt-get install gdb-multiarch

# install openocd
cd ../../../../
cd openocd
git checkout edb6796
./bootstrap
./configure --enable-cmsis-dap --enable-jaylink
make -j
sudo make install

# Install pretender dependencies
cd ../
cd pretender
git checkout graphFork
pip install -r requirements.txt
pip install -e .
cd ..

pip install -r requirements.txt

