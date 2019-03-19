import pprint

import serial
from conware.hardware import Arduino




if __name__ == "__main__":

    location = "ttyACM1"
    binary = ../
    due = Arduino(location)
    due.upload_binary()