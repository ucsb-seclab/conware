#!/bin/sh

#sudo apt-get install -y llvm>=3.8
cd runtime 
if [ ! -d cmake-3.13.4 ]; then 
	wget https://github.com/Kitware/CMake/releases/download/v3.13.4/cmake-3.13.4.tar.gz
	tar -xzvf cmake-3.13.4.tar.gz
fi

echo "Installing Ubuntu packages..."
sudo apt-get -y install graphviz direnv

echo "Installing ninja..."
sudo apt-get -y install ninja-build || (echo "Could not install ninja" && exit 0)


if [ ! -d llvm-7.0.1.src ]; then
	wget http://releases.llvm.org/7.0.1/llvm-7.0.1.src.tar.xz
	wget http://releases.llvm.org/7.0.1/cfe-7.0.1.src.tar.xz
	tar xf llvm-7.0.1.src.tar.xz
	tar xf cfe-7.0.1.src.tar.xz
	mv cfe-7.0.1.src llvm-7.0.1.src/tools/clang
fi


mkdir -p llvm-7.0.1.obj
cd llvm-7.0.1.obj
cmake -G Ninja -DCMAKE_BUILD_TYPE=Debug ../llvm-7.0.1.src
#make -j4
cmake --build .

cd .. # runtime
cd .. # back where we started

echo "export LLVM_SRC=$PWD/runtime/llvm-7.0.1.src" > .envrc
echo "export LLVM_OBJ=$PWD/runtime/llvm-7.0.1.obj" > .envrc
echo "export LLVM_DIR=$PWD/runtime/llvm-7.0.1.obj" > .envrc
echo "export ARM_GCC_TOOLCHAIN=$PWD/runtime/arduino-1.8.8/portable/packages/arduino/tools/arm-none-eabi-gcc/4.8.3-2014q1/bin" > .envrc
echo "export PYTHONPATH=$PYTHONPATH:$PWD/pretender:$PWD/conware:$PWD/avatar2-pretender" > .envrc
echo "PATH_add $PWD/runtime/llvm-7.0.1.obj/bin" > .envrc
echo "PATH_add $PWD/runtime/arduino-1.8.8/" > .envrc
echo "PATH_add $PWD/pretender/bin" > .envrc
echo "PATH_add $PWD/runtime/arduino-1.8.8/portable/packages/arduino/tools/bossac/1.6.1-arduino" > .envrc



direnv allow .

