#!/bin/sh
mkdir -p knock_and_ir
cd ..
conware-model-generate firmware/custom/knock/
conware-model-optimize firmware/custom/knock/model.pickle
conware-model-visualize firmware/custom/knock/model.pickle
conware-model-visualize firmware/custom/knock/model_optimized.pickle

conware-model-generate firmware/custom/irremote/
conware-model-optimize firmware/custom/irremote/model.pickle
conware-model-visualize firmware/custom/irremote/model.pickle
conware-model-visualize firmware/custom/irremote/model_optimized.pickle


conware-model-merge firmware/custom/knock/model.pickle firmware/custom/irremote/model.pickle -o experiments/knock_and_ir/knock_and_ir.pickle
conware-model-optimize experiments/knock_and_ir/knock_and_ir.pickle

conware-model-visualize experiments/knock_and_ir/knock_and_ir.pickle
conware-model-visualize experiments/knock_and_ir/knock_and_ir_optimized.pickle

mkdir -p experiments/knock_and_ir/knock
mkdir -p experiments/knock_and_ir/irremote
conware-emulate firmware/custom/knock/build_uninstrumented/knock.ino.bin -r experiments/knock_and_ir/knock -m experiments/knock_and_ir/knock_and_ir_optimized.pickle -t 120
conware-emulate firmware/custom/irremote/build_uninstrumented/irremote.ino.bin -r experiments/knock_and_ir/irremote -m experiments/knock_and_ir/knock_and_ir_optimized.pickle -t 120
