#!/bin/bash

for dir in ../firmware/custom/*
do
    dir_name=${dir##*/}     # remove the trailing "/"
    echo "Running $dir_name..."
    conware-model-generate $dir
    conware-model-optimize $dir/model.pickle
    conware-model-visualize $dir/model.pickle
    conware-model-visualize $dir/model_optimized.pickle
    conware-emulate $dir/build_uninstrumented/$dir_name.ino.bin  -r $dir -m $dir/model.pickle -t 600 -O emulated_output_linear.csv
    conware-emulate $dir/build_uninstrumented/$dir_name.ino.bin  -r $dir -m $dir/model_optimized.pickle -t 600 -O emulated_output.csv
done