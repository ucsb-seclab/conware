import serial

import logging

from pretender.logger import LogWriter

logger = logging.getLogger(__name__)


class Arduino:
    def __init__(self, device_location="ttyACM1"):
        self.device_location = device_location

    def upload_binary(self, binary_filename):
        ser = serial.Serial('/dev/%s' % self.device_location, baudrate=1200)
        ser.close()

        from subprocess import call
        call(["bossac", "-i", "-d",
              "--port=%s" % self.device_location, "-U", "false",
                                                        "-e", "-w", "-v", "-b",
              binary_filename, "-R"])

    def log_data(self, output_filename):
        ser = serial.Serial('/dev/%s' % self.device_location)

        dumping = False
        data_log = LogWriter(output_filename)
        dump_count = 0
        logger.info("Waiting for data to dump...")
        while True:
            try:
                line = ser.readline().strip("\r").strip("\n")
                if "CONWAREDUMP_START" in line:
                    logger.info("Dumping recording...")
                    dumping = True
                elif "CONWAREDUMP_END" in line:
                    logger.info("Dump done (%d events recorded)." % dump_count)
                    break
                elif dumping:
                    data = line.split("\t")
                    logger.debug(line)
                    data_log.write_row(data)
                    dump_count += 1
                else:
                    print line
            except KeyboardInterrupt:
                break
        data_log.close()
        ser.close()
