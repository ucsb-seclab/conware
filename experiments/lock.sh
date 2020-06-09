#!/bin/sh
mkdir -p lock
cd ..

conware-model-generate firmware/custom/knock/
conware-model-generate firmware/custom/irremote/
conware-model-generate firmware/custom/color_sensor/
conware-model-generate firmware/custom/servo/
conware-model-generate firmware/custom/blink2/

conware-model-merge firmware/custom/knock/model.pickle firmware/custom/irremote/model.pickle -o experiments/lock/knock_ir.pickle
conware-model-merge firmware/custom/color_sensor/model.pickle experiments/lock/knock_ir.pickle -o experiments/lock/knock_ir_color.pickle
conware-model-merge firmware/custom/servo/model.pickle experiments/lock/knock_ir_color.pickle -o experiments/lock/knock_ir_color_servo.pickle
conware-model-merge firmware/custom/blink2/model.pickle experiments/lock/knock_ir_color_servo.pickle -o experiments/lock/model.pickle
conware-model-optimize experiments/lock/model.pickle

conware-model-visualize experiments/lock/model.pickle
conware-model-visualize experiments/lock/model_optimized.pickle
python experiments uart_hack.py experiments/lock/model_optimized.pickle
conware-model-visualize experiments/lock/model_optimized_optimized_hacked.pickle

mkdir -p experiments/lock/knock
mkdir -p experiments/lock/irremote
mkdir -p experiments/lock/color_sensor
mkdir -p experiments/lock/servo
mkdir -p experiments/lock/blink2
mkdir -p experiments/lock/lock
conware-emulate firmware/custom/knock/build_uninstrumented/knock.ino.bin -r experiments/lock/knock -m experiments/lock/model_optimized.pickle -t 600
conware-emulate firmware/custom/irremote/build_uninstrumented/irremote.ino.bin -r experiments/lock/irremote -m experiments/lock/model_optimized.pickle -t 600
conware-emulate firmware/custom/color_sensor/build_uninstrumented/color_sensor.ino.bin -r experiments/lock/color_sensor -m experiments/lock/model_optimized.pickle -t 600
conware-emulate firmware/custom/servo/build_uninstrumented/servo.ino.bin -r experiments/lock/servo -m experiments/lock/model_optimized.pickle -t 600
conware-emulate firmware/custom/blink2/build_uninstrumented/blink2.ino.bin -r experiments/lock/blink2 -m experiments/lock/model_optimized.pickle -t 600
# Run the lock firmware
conware-emulate firmware/custom/lock/build_uninstrumented/lock.ino.bin -r experiments/lock/lock -m experiments/lock/model_optimized_hacked.pickle -t 2000
