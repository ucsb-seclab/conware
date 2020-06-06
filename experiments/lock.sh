#!/bin/sh
mkdir -p lock
cd ..

conware-model-generate firmware/custom/knock/
conware-model-generate firmware/custom/irremote/
conware-model-generate firmware/custom/color_sensor/

conware-model-merge firmware/custom/knock/model.pickle firmware/custom/irremote/model.pickle -o experiments/lock/knock_ir.pickle
conware-model-merge firmware/custom/color_sensor/model.pickle experiments/lock/knock_ir.pickle -o experiments/lock/model.pickle
conware-model-optimize experiments/lock/model.pickle

conware-model-visualize experiments/lock/model.pickle
conware-model-visualize experiments/lock/model_optimized.pickle

mkdir -p experiments/lock/knock
mkdir -p experiments/lock/irremote
mkdir -p experiments/lock/color_sensor
mkdir -p experiments/lock/lock
conware-emulate firmware/custom/knock/build_uninstrumented/knock.ino.bin -r experiments/lock/knock -m experiments/lock/model_optimized.pickle -t 1000
conware-emulate firmware/custom/irremote/build_uninstrumented/irremote.ino.bin -r experiments/lock/irremote -m experiments/lock/model_optimized.pickle -t 1000
conware-emulate firmware/custom/color_sensor/build_uninstrumented/color_sensor.ino.bin -r experiments/lock/color_sensor -m experiments/lock/model_optimized.pickle -t 1000

conware-emulate firmware/custom/lock/build_uninstrumented/lock.ino.bin -r experiments/lock/lock -m experiments/lock/model_optimized.pickle -t 1000
