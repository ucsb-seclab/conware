# Native
import logging
import os
import pickle

# Conware
import conware.globals as G

from conware.ground_truth.arduino_due import PeripheralMemoryMap
from conware.interrupts import Interrupter
from conware.tools.logger import LogReader
from conware.models.simple_storage import SimpleStorageModel
from conware.peripheral_model import PeripheralModel

logger = logging.getLogger(__name__)

peripheral_memory_map = PeripheralMemoryMap()


class ConwareModel:
    def __init__(self, name=None, address=None, size=None,
                 filename=None, **kwargs):
        self.peripherals = []
        self.model_per_address = {}
        self.model_per_interrupt = {}
        self.peripheral_clusters = {}
        self.log_per_cluster = {}
        self.accessed_addresses = set()
        self.stats = {
            'missed_reads': 0,
            'missed_writes': 0,
            'total_reads': 0,
            'total_writes': 0,
            'interrupts': 0
        }
        # filename = kwargs['kwargs']['filename'] if kwargs else None

        self.interrupt_map = kwargs['interrupt_map'] if kwargs and 'interrupt_map' in kwargs else {}

        # Load from disk?
        if filename is not None:
            self.__dict__ = pickle.load(open(filename, "rb"))
            # Reset all of our state!
            for p in self.peripherals:
                p.reset()
            # pprint.pprint(self.model_per_address)

        if "interrupt_map" not in self.__dict__:
            self.interrupt_map = {}

        self.host = kwargs['host'] if kwargs and 'host' in kwargs else None

    def __del__(self):
        self.shutdown()

    def __contains__(self, peripheral):
        """ Check to see if the given peripheral is in this model """
        return peripheral in self.peripherals

    def get_runtime_stats(self):
        for p in self.peripherals:
            self.stats[p.name] = p.stats
        return self.stats

    def add_peripheral(self, peripheral):
        """ Add a peripiheral to our list"""
        self.peripherals.append(peripheral)
        for addr in peripheral.addresses:
            self.model_per_address[addr] = peripheral

    def shutdown(self):
        pass

    def save(self, filename):
        """ Save our model to the specified directory """
        model_file = os.path.join(filename)
        logger.info("Saving model to %s", model_file)
        f = open(model_file, "wb+")
        pickle.dump(self.__dict__, f)
        f.close()

    def train(self, filename):
        """
        Train our model, potentially using a specific training model
        :return:
        """
        logger.info("Training hardware pretender (%s)" % filename)

        l = LogReader(filename)

        # Pop header
        l.next()

        # Step 0: Get a set of all of the addresses accessed
        for line in l:
            try:
                # ['Operation', 'Seqn', 'Address', 'Value', 'Value (Model)',
                # 'PC', 'Size', 'Timestamp', 'Model']
                op, id, addr, val, val_model, pc, size, timestamp, model = line
            except ValueError:
                logger.warning("Weird line: " + repr(line))
                continue
            if op in ["0", "1", "READ", "WRITE"]:
                self.accessed_addresses.add(int(addr, 16))
        l.close()

        if len(self.accessed_addresses) == 0:
            logger.error("No memory accesses were recorded!")
            return False

        # Step 1: Divide the possible addresses into peripherals
        used_peripherals = set()
        for addr in self.accessed_addresses:
            peripheral = peripheral_memory_map.get_peripheral(addr)
            if peripheral[0] not in used_peripherals:
                used_peripherals.add(peripheral[0])

        # Add our peripheral for each of its memory addresses
        for periph_name in peripheral_memory_map.peripheral_memory:
            if periph_name not in used_peripherals:
                continue
            logger.info("Packing peripheral %s" % periph_name)

            addrs = peripheral_memory_map.peripheral_memory[periph_name]
            addrs = set(range(addrs[0], addrs[1]))
            peripheral = PeripheralModel(addrs,
                                         name=periph_name)
            self.peripherals.append(peripheral)
            for addr in addrs:
                self.model_per_address[addr] = peripheral

            if periph_name in peripheral_memory_map.interrupt_map:
                for irq in peripheral_memory_map.interrupt_map[periph_name]:
                    self.model_per_interrupt[irq] = peripheral

        # Now add all of our observed accesses
        l = LogReader(filename)

        # Pop header
        l.next()

        # First, lets just build all of our states

        # Keep track of the last write seen, so that we can associate our interrupt with that write
        # While this may be the wrong state, we are hoping that triggering the interrupt based on write transitions
        # will be a close enough approximation to their asynchronous nature
        last_write_addr = None
        for line in l:
            # Extract our values form the log
            try:
                # ['Operation', 'Seqn', 'Address', 'Value', 'Value (Model)',
                # 'PC', 'Size', 'Timestamp', 'Model']
                op, id, addr, val, val_model, pc, size, timestamp, model = line
            except ValueError:
                logger.warning("Weird line: " + repr(line))
                continue

            # Convert to ints
            addr = int(addr, 16)
            val = int(val, 16)
            pc = int(pc, 16)

            # Handle writes
            if op in ["1", "WRITE"]:
                # state = self._create_state(addr, "write", val)
                self.model_per_address[addr].train_write(addr, val)
                last_write_addr = addr
            elif op in ["0", "READ"]:
                self.model_per_address[addr].train_read(addr, val, pc, size,
                                                        timestamp)
            elif op in ["2", "INTERRUPT"]:

                # If it's a mapping we have, ignore it, we already know when to trigger it
                if val in self.interrupt_map:
                    logger.debug("Found mapped interrupt (0x%08X), skipping" % val)
                    continue
                # Do we know which peripheral this goes with?
                elif val in self.model_per_interrupt:
                    logger.info("Trained interrupt (%s)" % str(irq))
                    self.model_per_interrupt[irq].train_interrupt(val, timestamp)
                else:
                    logger.warning("Got interrupt %s and it is not mapped to a peripheral! " % str(irq))
                    self.model_per_address[last_write_addr].train_interrupt(val, timestamp)

            else:
                logger.error("Saw an unrecognized operation (%s)!" % op)

        l.close()

        for idx, peripheral in enumerate(self.peripherals):
            peripheral.train()
            self.peripherals[idx] = peripheral
        #     peripheral.merge_states()

        return True

    def get_model(self, address):
        """
        return the name of the model that is controlling the address
        :param address:
        :return:
        """

        if address in self.model_per_address:
            return repr(self.model_per_address[address])
        else:
            return None

    def get_interrupts(self, address):
        """"
            Return a dictionary of all of the interrupts in the current state, with their counts
            :param address: Address that return the interrupts for the current state for
            :return:
        """
        if address in self.model_per_address:
            if isinstance(self.model_per_address[address], SimpleStorageModel):
                return {}
            return self.model_per_address[address].get_interrupts()
        else:
            return {}

    def write_memory(self, address, size, value):
        """
        On a write, we need to check if this value affects any other address
        return values and update the state accordingly

        :param address:
        :param size:
        :param value:
        :return:
        """
        logger.debug("Write %s %s %s" % (address, size, value))
        self.stats['total_writes'] += 1

        if address not in self.model_per_address:
            self.stats['missed_writes'] += 1
            logger.debug(
                "No model found for %s, using SimpleStorageModel...",
                hex(address))
            self.model_per_address[address] = SimpleStorageModel()
            rtn = True
        else:
            if isinstance(self.model_per_address[address], PeripheralModel):
                rtn = self.model_per_address[address].write(address, size,
                                                            value)
            else:
                rtn = self.model_per_address[address].write(value)

        # Inject an interrupt?
        if (address, value) in self.interrupt_map:
            self.stats['interrupts'] += 1
            logger.info("Injecting interrupt!")
            logger.info(self.host)
            irq_num = self.interrupt_map[(address, value)]
            i = Interrupter(irq_num, self.host, count=1)
            i.start()

        return rtn

    def read_memory(self, address, size):
        """
        On a read, we will use our model to return an appropriate value

        :param address:
        :param size:
        :return:
        """
        logger.debug("Read %s %s" % (address, size))
        self.stats['total_reads'] += 1

        if address not in self.model_per_address:
            self.stats['missed_reads'] += 1
            logger.debug(
                "No model found for %s, using SimpleStorageModel...",
                hex(address))
            self.model_per_address[address] = SimpleStorageModel()
            print "No model found for %s, using SimpleStorageModel..." % hex(
                address)

        if isinstance(self.model_per_address[address], PeripheralModel):
            return self.model_per_address[address].read(address, size)
        else:
            return self.model_per_address[address].read()

        # An address we've never seen, or couldn't determine a model?
        # Let's just call it storage
        if address not in self.model_per_address or self.model_per_address[
            address]['model'] is None:
            logger.debug(
                "No model found for %s, using SimpleStorageModel...",
                hex(address))
            self.__init_address(address)
            self.model_per_address[address]['model'] = SimpleStorageModel()

        return self.model_per_address[address]['model'].read()

    def get_peripherals(self):
        return self.peripherals
