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
        if address is not None and value is not None:
            self.name = "%s:%s:%#x" % (operation, hex(address), value)
        else:
            self.name = operation
        self.operation = operation
        self.address = address
        self.value = value
        self.reads = {}
        self.read_count = {}
        self.model_per_address_ordered = {}
        self.model_per_address = {}

        self.merged_states = set()
        self.merged_states.add(state_id)
        self.interrupts = {}

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
        interrupts = ""
        if len(self.interrupts.keys()) > 0:
            interrupts = " | " + str(self.interrupts)
        return "%s, #%d " % (str(self.state_id), len(self.merged_states)) + ",".join(models) + interrupts

    def __repr__(self):
        return self.__str__()

    def __ne__(self, other_state):
        """ See if they are NOT equal """
        return not (self == other_state)

    def __eq__(self, other_state):

        # Do not consider an empty node equal to a non-empty node
        # Otherwise, merging nodes with different reads is fine
        if (len(self.model_per_address.keys()) == 0 and len(other_state.model_per_address.keys()) != 0) or \
                (len(other_state.model_per_address.keys()) == 0 and len(self.model_per_address.keys()) != 0):
            return False

        # Make sure all of our read models are equivalent
        for address in self.model_per_address:
            if address in other_state.model_per_address:
                if self.model_per_address[address] != \
                        other_state.model_per_address[address]:
                    return False

        # Make sure that we have the same interrupt numbers
        if set(self.interrupts.keys()) != set(other_state.interrupts.keys()):
            return False

        # for address in self.model_per_address_ordered:
        #     if address in other_state.model_per_address_ordered and \
        #             self.model_per_address_ordered[address] != \
        #             other_state.model_per_address_ordered[address]:
        #         return False
        return True

    def is_empty(self):
        return len(self.model_per_address) == 0

    def _train_model(self, address, read_log, use_time_domain=True):
        if len(read_log) == 0:
            return None

        # Check if just storage
        # It's storage if the value always equals the write value that created this state,
        # or this in the "start" state, which has self.value = None
        storage = True
        last_value = None
        for val, pc, size, timestamp in read_log:
            if (address != self.address or int(val) != int(self.value)) and self.value is not None:
                storage = False
                break
            if self.value is None and last_value is not None and last_value != int(val):
                storage = False
                break
            last_value = int(val)

        if storage:
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

    def append_interrupt(self, irq_num):
        """
        add an interrupt to fire once this state is entered

        If the same interrupt is added multiple times
        :param irq_num: Number of IRQ to fire
        :return:
        """
        if irq_num not in self.interrupts:
            self.interrupts[irq_num] = 1
        else:
            self.interrupts[irq_num] += 1

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

        # Merge any interrupts (if each state had 1 interrupt, we'd now to initiate 2)
        for irq_num in self.interrupts:
            self.interrupts[irq_num] = max(self.interrupts[irq_num],
                                           other.interrupts[irq_num])
        self.merged_states |= other.merged_states

        return True
