import csv
import logging

logger = logging.getLogger(__name__)


class PretenderLog:
    HEADER = ['Operation', 'Seqn', 'Address', 'Value', 'Value (Model)',
              'PC', 'Size', 'Timestamp', 'Model']

    def __init__(self):
        pass


class LogWriter(PretenderLog):
    """
    Write CSV logs in our standard format
    """

    def __init__(self, filename, buffer=True):
        if not buffer:
            self.csvfile = open(filename, 'wb', 0)  # 0 for no buffer
        self.csvfile = open(filename, 'wb')
        self.writer = csv.writer(self.csvfile, delimiter='\t',
                                 quotechar='|', quoting=csv.QUOTE_MINIMAL)
        self.writer.writerow(self.HEADER)

    def write_row(self, row):
        """
        Write a list of values to our log file
        :param row:
        :return:
        """
        if len(row) != len(self.HEADER):
            logger.warning("The row written does not match our format: %s" %
                           repr(self.HEADER))
        self.writer.writerow(row)

    def close(self):
        # self.file.close()
        self.csvfile.close()


class LogReader(PretenderLog):
    """
        Read CSV logs in our standard format
    """

    def __init__(self, filename):
        self.csvfile = open(filename, 'rb')
        self.reader = csv.reader(self.csvfile, delimiter='\t',
                                 quotechar='|', quoting=csv.QUOTE_MINIMAL)

    def __iter__(self):
        return self

    def next(self):
        return self.read_row()

    def close(self):
        # self.file.close()
        self.csvfile.close()

    def read_row(self):
        return self.reader.next()
