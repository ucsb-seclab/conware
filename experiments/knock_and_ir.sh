#!/bin/sh
mkdir -p knock_and_ir
cd ..
conware-model-generate firmware/custom/knock/
conware-model-generate firmware/custom/irremote/

conware-model-merge firmware/custom/knock/model.pickle firmware/custom/irremote/model.pickle -o experiments/knock_and_ir/knock_and_ir.pickle
conware-model-optimize experiments/knock_and_ir/knock_and_ir.pickle

conware-model-visualize experiments/knock_and_ir/knock_and_ir.pickle
conware-model-visualize experiments/knock_and_ir/knock_and_ir_optimized.pickle

