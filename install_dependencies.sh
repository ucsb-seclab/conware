#!/bin/sh

# First, let's get our submodules
git submodule update --init --recursive

#sudo apt-get install -y llvm>=3.8
cd runtime 


echo "Installing Ubuntu packages..."
# if there is no cmake command, install it
if type cmake >/dev/null 2>&1; then
	echo "cmake already installed"
else
	echo "cmake not installed..."
	sudo apt-get install -y cmake
fi
sudo apt-get -y install graphviz direnv
sudo apt-get install -y libc6-dev-i386 

# Requirement for graphviz
sudo apt-get install graphviz-dev

# For graphviz to print pdf
sudo apt-get install libcairo2-dev
sudo apt-get install libpango1.0-dev


echo "Installing ninja..."
sudo apt-get -y install ninja-build || (echo "Could not install ninja" && exit 0)


if [ ! -d llvm-7.0.1.src ]; then
	wget http://releases.llvm.org/7.0.1/llvm-7.0.1.src.tar.xz
	wget http://releases.llvm.org/7.0.1/cfe-7.0.1.src.tar.xz
	tar xf llvm-7.0.1.src.tar.xz
	tar xf cfe-7.0.1.src.tar.xz
	rm llvm-7.0.1.src.tar.xz
	rm llvm-7.0.1.src.tar.xz
	mv cfe-7.0.1.src llvm-7.0.1.src/tools/clang
fi


mkdir -p llvm-7.0.1.obj
cd llvm-7.0.1.obj
cmake -G Ninja ../llvm-7.0.1.src

# This did not work on a multi-core machine (it spawned too many processes)
#cmake --build .

# capping l to 15 limited the use of multiple cores (to not tap exhaust the RAM)
ninja -l 1

cd .. # runtime
cd .. # back where we started

echo "export LLVM_SRC=$PWD/runtime/llvm-7.0.1.src" > .envrc
echo "export LLVM_OBJ=$PWD/runtime/llvm-7.0.1.obj" >> .envrc
echo "export LLVM_DIR=$PWD/runtime/llvm-7.0.1.obj" >> .envrc
echo "export ARM_GCC_TOOLCHAIN=$PWD/runtime/arduino-1.8.8/portable/packages/arduino/tools/arm-none-eabi-gcc/4.8.3-2014q1/bin" >> .envrc
echo "export PYTHONPATH=$PYTHONPATH:$PWD/pretender:$PWD/conware:$PWD/avatar2-pretender" >> .envrc
echo "PATH_add $PWD/runtime/llvm-7.0.1.obj/bin" >> .envrc
echo "PATH_add $PWD/runtime/arduino-1.8.8/" >> .envrc
echo "PATH_add $PWD/pretender/bin" >> .envrc
echo "PATH_add $PWD/conware/bin" >> .envrc
echo "PATH_add $PWD/runtime/arduino-1.8.8/portable/packages/arduino/tools/bossac/1.6.1-arduino" >> .envrc



direnv allow .

