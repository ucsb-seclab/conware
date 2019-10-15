import logging
import sys

#We import all these pretender models (incresing, markov, pattern, simple...
#Do we want to use them or just use all network X

logger = logging.getLogger(__name__)


class PeripheralModelState2:
    """
    Simple state object for each peripheral state
    """

    def __init__(self, address, operation, value):
        self.name = "%s:%s:%#x" % (operation, hex(address), value)
        self.operation = operation
        self.value = value
        self.reads = {}
        self.read_count = {}
        self.addresses = []



    def append_read(self, address, value, pc, size, timestamp):
        if address not in self.reads:
            self.reads[address] = {}
        if address not in self.read_count:
            self.read_count[address] = 0
        if self.read_count[address] not in self.reads[address]:
            self.reads[address][self.read_count[address]] = []

        self.reads[address][self.read_count[address]].append((value, pc, size, timestamp))

        self.read_count[address] += 1
