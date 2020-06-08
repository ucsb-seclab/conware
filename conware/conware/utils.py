import csv
import logging

from conware.model import peripheral_memory_map

logger = logging.getLogger(__name__)


# emulated log: Operation Seqn	Address	Value	Value (Model)	PC	Size	Timestamp	Model /////////This is a tsv file
# recorded log: Operation	Seqn	Address	Value	Value (Model)	PC	Size	Timestamp	Model ///////// this is listed as a csv file but it is a tsv file


def get_log_stats(recording_filename):
    """
    return compiled MMIO stats from a log
    :param recording_filename:
    :return:
    """
    recording = file(recording_filename, 'r')

    recording_csv = csv.reader(recording, dialect=csv.excel_tab)

    # Skip headers
    recording_csv.next()

    addresses = {}
    address_values = {}
    writes = {}
    write_values = {}
    reads = {}
    read_values = {}
    interrupts = {}
    interrupt_values = {}

    total = 0
    total_read = 0
    total_write = 0
    for line in recording_csv:
        total += 1
        # print line
        op, id, addr, val, val_model, pc, size, timestamp, model = line

        # Addresses
        if addr not in addresses:
            addresses[addr] = 0
        if (addr, val) not in address_values:
            address_values[(addr, val)] = 0
        addresses[addr] += 1
        address_values[(addr, val)] += 1

        # Writes
        if op in ["1", "WRITE"]:
            if addr not in writes:
                writes[addr] = 0
            if (addr, val) not in write_values:
                write_values[(addr, val)] = 0

            writes[addr] += 1
            write_values[(addr, val)] += 1
            total_write += 1

        elif op in ["0", "READ"]:
            if addr not in reads:
                reads[addr] = 0
            if (addr, val) not in read_values:
                read_values[(addr, val)] = 0

            reads[addr] += 1
            read_values[(addr, val)] += 1
            total_read += 1

        elif op in ["2", "INTERRUPT"]:
            if val not in interrupts:
                interrupts[val] = 0

            interrupts += 1

    peripherals = set()
    for a in addresses:
        peripherals.add(peripheral_memory_map.get_peripheral(int(a, 16))[0])

    print "Peripherals: ", len(peripherals), peripherals
    print "Addresses: ", len(addresses)
    print "Address/value pairs: ", len(address_values)
    print "Writes: ", len(writes)
    print "Write/value pairs: ", len(write_values)
    print "Reads: ", len(reads)
    print "Read/value pairs: ", len(read_values)
    print "Interrupts: ", len(interrupts)
    print "Total lines:", total
    print "Total reads: ", total_read

    return {'peripherals': peripherals,
            'addresses': addresses,
            'address_values': address_values,
            'writes': writes,
            'write_values': write_values,
            'reads': reads,
            'read_values': read_values,
            'interrupts': interrupts,
            'total_lines': total,
            'total_reads': total_read,
            'total_writes': total_write}


def get_log_diff(emulated, recorded, output_file):
    """
    Compare the two logs based on each peripheral and compare their logs in order
    :param emulated:
    :param recorded:
    :param output_file:
    :return:
    """

    recorded_reads = []
    recorded_reads_referecne = {}
    recorded_writes = []
    recorded_writes_reference = {}
    emulated_reads = []
    emulated_writes = []
    count = 0
    total_emulated = 0
    total_recorded = 0

    if output_file is not None:
        out = open(output_file, "w+")
    else:
        out = None
    emulated_log = file(emulated, 'r')
    recorded_log = file(recorded, 'r')

    emulated_csv = csv.reader(emulated_log, dialect=csv.excel_tab)
    recorded_csv = csv.reader(recorded_log, dialect=csv.excel_tab)

    # Skip headers
    next(emulated_csv)
    next(recorded_csv)

    recorded_dict = {k: [] for k in peripheral_memory_map.peripheral_memory}
    emulated_dict = {k: [] for k in peripheral_memory_map.peripheral_memory}

    # Read relevant tuples from recording
    for row in recorded_csv:
        operation, address, value = (row[i] for i in (0, 2, 3))
        address = int(address, 16)
        value = int(value, 16)
        peripheral_name = peripheral_memory_map.get_peripheral(address, value)
        if peripheral_name is None:
            if address != 0:
                logger.warning("Found address with no mapped peripheral! (%s)" % (address, value))
            continue
        else:
            peripheral_name = peripheral_name[0]
        recorded_dict[peripheral_name].append((operation, address, value))
        total_recorded += 1
        # if row[0] == 'READ':
        #     recorded_reads.append([row[2], row[3], row[6]])
        # elif row[0] == 'WRITE':
        #     recorded_writes.append([row[2], row[3], row[6]])

    # Read relevant tuples from emulated output
    for row in emulated_csv:
        operation, address, value = (row[i] for i in (0, 2, 3))
        address = int(address, 16)
        value = int(value, 16)
        peripheral_name = peripheral_memory_map.get_peripheral(address, value)
        if peripheral_name is None:
            if address != 0:
                logger.warning("Found address with no mapped peripheral! (%s)" % (address, value))
            continue
        else:
            peripheral_name = peripheral_name[0]
        emulated_dict[peripheral_name].append((operation, address, value))
        total_emulated += 1
        # if row[0] == 'READ':
        #     emulated_reads.append([row[2], row[3], row[6]])
        # elif row[0] == 'WRITE':
        #     emulated_writes.append([row[2], row[3], row[6]])

    not_equal_count = 0
    repeat_count = 0

    missing_emulated = 0
    missing_recorded = 0
    conflicts = 0
    total_compared = 0
    for peripheral_name in peripheral_memory_map.peripheral_memory:
        logger.debug("*Checking %s (%d entries vs %d entries)..." % (peripheral_name,
                                                                     len(emulated_dict[peripheral_name]),
                                                                     len(recorded_dict[peripheral_name])
                                                                     ))
        idx_emulated = 0
        idx_recorded = 0
        emulated_tuples = emulated_dict[peripheral_name]
        recorded_tuples = recorded_dict[peripheral_name]
        while idx_recorded < len(recorded_tuples) and \
                idx_emulated < len(emulated_tuples):
            op_emu, addr_emu, value_emu = emulated_tuples[idx_emulated]

            op_rec, addr_rec, value_rec = recorded_tuples[idx_recorded]

            if op_rec == op_emu and addr_rec == addr_emu:
                if value_emu != value_rec:
                    # Let's check to see if we have any duplicate values (e.g.,
                    # status registers)

                    # Check to see if emulated keeps repeating
                    idx_tmp = idx_emulated
                    while idx_tmp < len(emulated_tuples) and emulated_tuples[
                        idx_tmp] == (op_emu, addr_emu, value_emu):
                        idx_tmp += 1
                    if idx_tmp == len(emulated_tuples):
                        logger.info(
                            "Hit end of emulated log (%d early)" % (idx_tmp -
                                                                    idx_emulated))
                        break
                    # Looks like we just had a long repeat
                    if recorded_tuples[idx_recorded] == emulated_tuples[idx_tmp]:
                        logger.debug("Skipped %d lines in emulated output." %
                                     (idx_tmp - idx_emulated))
                        repeat_count += idx_tmp - idx_emulated
                        idx_emulated = idx_tmp
                        continue

                    # Check to see if the recording keeps repeating
                    idx_tmp = idx_recorded
                    while idx_tmp < len(recorded_tuples) and recorded_tuples[
                        idx_tmp] == (op_rec, addr_rec, value_rec):
                        idx_tmp += 1
                    # Looks like we just had a few repeats
                    if idx_tmp == len(recorded_tuples):
                        logger.info(
                            "Hit end of recorded log (%d early)" % (idx_tmp -
                                                                    idx_recorded))
                        break
                    if recorded_tuples[idx_recorded] == emulated_tuples[idx_tmp]:
                        logger.debug("Skipped %d lines in recorded output." %
                                     (idx_tmp - idx_recorded))
                        repeat_count += idx_tmp - idx_recorded
                        idx_recorded = idx_tmp
                        continue

                    logger.warning("Found unequal rows %s != %s" % (
                        recorded_tuples[idx_recorded],
                        emulated_tuples[idx_emulated]))
                    logger.warning("%d\t%s\t%d\t%s\n" % (idx_recorded, recorded_tuples[idx_recorded],
                                                         idx_emulated, emulated_tuples[idx_emulated]))

                    conflicts += 1
                    if out is not None:
                        out.write("%d\t%s\t%d\t%s\n" % (idx_emulated, emulated_tuples[idx_emulated],
                                                        idx_recorded, recorded_tuples[idx_recorded]))
                    # Hum... they never synced up?
                    not_equal_count += 1
                    idx_emulated += 1
                    idx_recorded += 1
                else:
                    # Equal!
                    idx_emulated += 1
                    idx_recorded += 1
                    continue
            else:
                # Let's advance until they sync up again
                next_emu = idx_emulated
                next_rec = idx_recorded

                # Find the next index in each that makes them both equal
                while next_emu < len(emulated_tuples) and \
                        emulated_tuples[next_emu] != recorded_tuples[idx_recorded]:
                    next_emu += 1

                while next_rec < len(recorded_tuples) and \
                        recorded_tuples[next_rec] != emulated_tuples[idx_emulated]:
                    next_rec += 1

                # Increment the smallest jump in the sequence
                if (next_rec - idx_recorded) < (next_emu - idx_emulated):
                    logger.warning("%d lines missing from emulated @ %d." % (
                        next_rec - idx_recorded, idx_emulated))
                    missing_emulated += next_rec - idx_recorded

                    not_equal_count += next_rec - idx_recorded
                    while idx_recorded < next_rec:
                        logger.info("%d: %s 0x%08X 0x%08X" % ((idx_recorded + 1,
                                                               ) + recorded_tuples[idx_recorded]))
                        idx_recorded += 1
                    continue
                else:
                    logger.warning("%d lines missing from recording. @ %d" % (
                        next_emu - idx_emulated, idx_recorded))
                    missing_recorded += next_emu - idx_emulated
                    not_equal_count = next_emu - idx_emulated
                    while idx_emulated < next_emu:
                        logger.info("%d: %s 0x%08X 0x%08X" % (
                                (idx_emulated + 1,) + emulated_tuples[
                            idx_emulated]))
                        idx_emulated += 1
                    continue

            # logger.error("Pretty sure this should never happen...")
            not_equal_count += 1
            idx_emulated += 1
            idx_recorded += 1
            continue
        total_compared += max(idx_recorded, idx_emulated)

    print "Total: %d" % total_compared
    print "Conflicts: %d, Missing emulated: %d, Missing recording: %d" % (conflicts, missing_emulated, missing_recorded)

    return {'total': total_compared,
            'conflicts': conflicts,
            'missing_emulated': missing_emulated,
            'missing_recorded': missing_recorded,
            'total_emulated': total_emulated,
            'total_recorded': total_recorded}
