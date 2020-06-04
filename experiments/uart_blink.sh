#!/bin/sh
mkdir -p uart_blink

cp ../firmware/custom/blink/recording.tsv uart_blink
cp ../firmware/custom/blink/model.pickle uart_blink
cp ../firmware/custom/blink/model_optimized.pickle blink_knock
conware-emulate ../firmware/custom/blink/build/blink.ino.bin  -r blink_knock -m blink_knock/model.pickle -O emulated_output_linear.csv
conware-emulate ../firmware/custom/blink/build/blink.ino.bin  -r blink_knock -m blink_knock/model_optimized.pickle
python log_diff.py .