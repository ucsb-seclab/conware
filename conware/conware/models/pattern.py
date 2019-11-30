import logging
import random

# Conware
from conware.models import MemoryModel

logger = logging.getLogger(__name__)


class PatternModel(MemoryModel):
    def __init__(self, init_value=0, address=None):
        self.value = init_value
        # self.read_pattern = []
        self.encoded_pattern = []
        self.count = 0
        self.index = 0
        self.read_patterns = {self.value: []}

    def __str__(self):
        if len(self.read_patterns[self.value]) == 0:
            return "<PatternModel (empty)>"
        elif len(self.read_patterns[self.value][self.index]) > 5:
            return "<PatternModel (%s) [%d items]>" % (",".join(
                [str(x) for x in self.read_patterns.keys()]), len(
                self.read_patterns[self.value][self.index]))
        else:
            return "<PatternModel (%s) %s>" % (",".join(
                [str(x) for x in self.read_patterns.keys()]),
                                               self.read_patterns[
                                                   self.value][
                                                   self.index])

    def __repr__(self):
        return self.__str__()

    def __eq__(self, other_model):
        if type(other_model) != type(self):
            return False
        if self.read_patterns[self.value][self.index] == \
                other_model.read_patterns[other_model.value][other_model.index]:
            return True
        else:
            if len(self.encoded_pattern) != len(other_model.encoded_pattern):
                return False
            for idx, x in enumerate(self.encoded_pattern):
                if x[0] != \
                        other_model.encoded_pattern[idx][0]:
                    return False

        return True

    def write(self, address, value):
        """
        Update which specific pattern we are returning
        This should help our replays be more realistic as the pattern will be
        dependent on the write value that brought us into the state.

        :param address:
        :param value:
        :return:
        """

        # have we seen this value?
        if value in self.read_patterns:
            self.value = value
            # Do we have more than one option?  Pick one randomly
            if len(self.read_patterns[value]) > 1:
                logger.debug("Updated to random read pattern.")
                self.index = random.randint(0,
                                            len(self.read_patterns[value]) - 1)
            else:
                self.index = 0
        else:
            # Value we've never seen, let's just pick one.
            self.value = random.choice(self.read_patterns.keys())
            logger.debug("Saw a write that we've never seen before (%08X), "
                           "randomly selected %d." % (value, self.value))
        return True

    def read(self):
        idx = self.count % len(self.read_patterns[self.value][self.index])
        self.count += 1
        return self.read_patterns[self.value][self.index][idx]

    def merge(self, other_model):
        if other_model != self:
            logger.error("Tried to merge two models that aren't the same (%s "
                         "!= %s)" % (type(other_model), type(self)))
            return False

        for value in other_model.read_patterns:
            # Add the pattern from the other
            if value not in self.read_patterns:
                self.read_patterns[value] = \
                    other_model.read_patterns[other_model.value]
            else:
                for pattern in other_model.read_patterns[value]:
                    if pattern not in self.read_patterns[value]:
                        self.read_patterns[value].append(pattern)

        return True

    def train(self, log):
        """
        Attempt to try a pattern model, or return False if no pattern is
        detected

        :param log:
        :return:
        """

        # Only extract our read values
        reads = [x[0] for x in log]

        read_pattern = self.get_pattern(reads)

        if read_pattern is None:
            return False
        else:
            # Now let's encode our pattern
            pattern = []
            last = None
            repeated_value = None
            repeated_count = 0
            for x in read_pattern:
                if x == last:
                    repeated_count += 1
                else:
                    if last is not None:
                        pattern.append((last, repeated_count))
                    last = x
                    repeated_count = 1
            pattern.append((last, repeated_count))

            self.read_patterns[self.value].append(read_pattern)
            self.encoded_pattern = pattern
            return True

    @staticmethod
    def get_pattern(reads):
        """
        Extract a pattern out of a stream of read values

        NOTE: We assume that any stream is a pattern!  When merging we will
        find out if the pattern is the wrong thing to do.

        :param reads:
        :return:
        """
        # Are they all the same?
        all_same = True
        for x in reads:
            if x != reads[0]:
                all_same = False
        if all_same:
            return [reads[0]]

        # Let's see if a repeating pattern exist
        max_len = len(reads) / 2
        for seqn_len in range(2, max_len):

            # Do the first 2 at least match as a pattern?
            if reads[0:seqn_len] == reads[seqn_len:2 * seqn_len]:

                is_pattern = True

                # Let's check all the others, ignoring any incomplete
                # patterns at the end
                last_complete_seqn = len(reads) - len(reads) % seqn_len
                for y in range(2 * seqn_len, last_complete_seqn, seqn_len):
                    if reads[0:seqn_len] != reads[y:y + seqn_len]:
                        is_pattern = False
                        break
                remainder = reads[-(len(reads) % seqn_len):]
                if not all(remainder[i] == reads[i] for i in
                           range(len(remainder))):
                    is_pattern = False
                if is_pattern:
                    return reads[0:seqn_len]

        return reads

    @staticmethod
    def fits_model(log):
        """
        Determine if the reads always return some fixed pattern.

        For now, we are ignoring writes; however, we should clearly
        incorporate them in the future, maybe even a different model

        @TODO Incorporate writes?

        :param log:
        :return:
        """

        # if len(reads) < 2:
        #     return False

        # Only extract our read values
        reads = [x[0] for x in log]

        return PatternModel.get_pattern(reads) is not None
