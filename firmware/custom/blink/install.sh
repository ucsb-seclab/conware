#!/bin/sh
../arduino-1.8.8/arduino --board arduino:avr:uno --port /dev/ttyACM0 --upload *.ino 
#screen /dev/ttyACM0 9600
