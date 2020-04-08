# Native
import logging
import sys

# Conware
from conware.models.increasing import IncreasingModel
from conware.models.markov2 import MarkovModel
from conware.models.markovpattern import MarkovPatternModel
from conware.models.pattern import PatternModel
from conware.models.simple_storage import SimpleStorageModel

logger = logging.getLogger(__name__)


class PeripheralModelState:
    """
    Simple state object for each peripheral state
    """
    state_number = 0

    def __init__(self, address, operation, value, state_id):
        self.state_id = state_id
        self.name = "%s:%s:%#x" % (operation, hex(address), value)
        self.operation = operation
        self.address = address
        self.value = value
        self.reads = {}
        self.read_count = {}
        self.model_per_address_ordered = {}
        self.model_per_address = {}

        self.merged_states = set()
        self.merged_states.add(state_id)

        # state number imported from old state model, not sure if we need it
        # was used for visualization purposes, i haven't dove very deep into all
        # of the different visualizations, just UART
        self.state_number = PeripheralModelState.state_number
        PeripheralModelState.state_number += 1

    def __str__(self):
        models = []
        for address in self.model_per_address:
            models.append(
                "0x%08X: %s" % (address, self.model_per_address[address]))

        # return ":".join([str(x) for x in sorted(self.merged_states)]) + " " + \
        return "#%d " % len(self.merged_states) + ",".join(models)

    def __repr__(self):
        return self.__str__()

    def __ne__(self, other_state):
        """ See if they are NOT equal """
        return not (self == other_state)

    def __eq__(self, other_state):
        for address in self.model_per_address:
            if address in other_state.model_per_address:
                if self.model_per_address[address] != \
                        other_state.model_per_address[address]:
                    return False
        # for address in self.model_per_address_ordered:
        #     if address in other_state.model_per_address_ordered and \
        #             self.model_per_address_ordered[address] != \
        #             other_state.model_per_address_ordered[address]:
        #         return False
        return True

    def _train_model(self, address, read_log, use_time_domain=True):
        if len(read_log) == 0:
            return None

        # Check if just storage
        # Either this is the address that is on the incoming write edge, and the read value is always the write value,
        # or it always reads the same exact value
        storage = True
        last_value = None
        for val, pc, size, timestamp in read_log:
            if self.address == address and int(val) != int(self.value):
                storage = False
                break
            if last_value is not None and last_value != int(val):
                storage = False
                break
            last_value = int(val)

        if storage or len(read_log) == 1 :
            m = SimpleStorageModel(self.value)
            m.train(read_log)
            logger.debug("State %s is StorageModel" % self.state_id)
            return m

        # Try Other Models
        if use_time_domain:
            for model in [PatternModel, IncreasingModel, MarkovPatternModel,
                          MarkovModel]:
                m = model(self.value)
                logger.debug("Trying model %s" % repr(m))
                if m.train(read_log):
                    logger.info("%s is %s" % (self.name, repr(m)))
                    return m
        else:
            for model in [MarkovModel]:
                m = model()
                if m.train(read_log):
                    # logger.info("%s is %s" % (self.name, repr(model)))
                    return m

    def append_read(self, address, value, pc, size, timestamp):
        if address not in self.reads:
            self.reads[address] = {}
        if address not in self.read_count:
            self.read_count[address] = 0
        if self.read_count[address] not in self.reads[address]:
            self.reads[address][self.read_count[address]] = []

        self.reads[address][self.read_count[address]].append(
            (value, pc, size, timestamp))

        self.read_count[address] += 1

    def train(self):
        for address in self.reads:
            if address not in self.model_per_address_ordered:
                self.model_per_address_ordered[address] = {}

            combined_reads = []  # aggregate of all reads
            for read_count in self.reads[address]:
                combined_reads += self.reads[address][read_count]
            #     reads = self.reads[address][read_count]
            #
            #     # Set Model for ordered Reads
            #     m = self._train_model(reads, use_time_domain=False)
            #     self.model_per_address_ordered[address][read_count] = m

            # Set Model for unordered reads
            m = self._train_model(address, combined_reads)
            self.model_per_address[address] = m

    def reset(self):
        for addr in self.read_count:
            self.read_count[addr] = 0

    def merge(self, other):
        """

        :param other: The `other` state to merge
        :return:
        """
        logger.debug("Merging %s into %s" % (other, self))
        # Are they the same state?
        if self.state_id == other.state_id:
            logger.warn("Tried to merge identical states!")
            return False

        # merge any duplicate address
        for address in self.model_per_address:
            if address in other.model_per_address:
                self.model_per_address[address].merge(
                    other.model_per_address[address])
        # for address in self.model_per_address_ordered:
        #     if address in other.model_per_address_ordered:
        #         self.model_per_address_ordered[address].merge(
        #             other.model_per_address_ordered[address])

        # Copy any new addresses
        for address in other.model_per_address:
            if address not in self.model_per_address:
                self.model_per_address[address] = other.model_per_address[
                    address]
        # for address in other.model_per_address_ordered:
        #     if address not in self.model_per_address_ordered:
        #         self.model_per_address_ordered[address] = \
        #             other.model_per_address_ordered[address]

        self.merged_states |= other.merged_states
        return True
