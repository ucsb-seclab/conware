#!/bin/sh

tty=ttyACM0
baud=1200
# Set up device
stty -F /dev/$tty $baud

./runtime/arduino-1.8.8/portable/packages/arduino/tools/bossac/1.6.1-arduino/bossac -i -d --port=$tty -U false -e -w -v -b $1 -R

#screen /dev/$tty 9600
