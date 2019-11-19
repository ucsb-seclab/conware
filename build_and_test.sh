#!/bin/sh
vf activate conware
root=$PWD
./rebuild_runtime.sh || exit 1
./instrument_project.sh firmware/custom/blink/ || exit 1
python conware/bin/conware-recorder firmware/custom/blink/ 
