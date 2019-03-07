#!/bin/sh

tty=ttyACM1
baud=1200
# Set up device
stty -F /dev/$tty $baud

# Let cat read the device $1 in the background
cat /dev/$tty &

# Capture PID of background process so it is possible to terminate it when done
bgPid=$!

# Terminate background read process
kill $bgPid

./runtime/arduino-1.8.8/portable/packages/arduino/tools/bossac/1.6.1-arduino/bossac -i -d --port=$tty -U false -e -w -v -b $1 -R

