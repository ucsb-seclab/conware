#!/bin/sh

for dir in lock/*/
do
    echo $dir
    dir_name=${dir%*/}
#    dir_name=${dir##*/}     # remove the trailing "/"
    echo "Running $dir..."
    python conware-mmio-counter.py $dir/emulated_output.csv ${dir_name}_mmio_count.pdf
done
