# These are the hooks for recording and replay
import os

#import pretender.globals as G
import conware.globals as G

import logging
import time

l = logging.getLogger("pretender.hooks")
logger = l
seq = 0

ignored_ranges = []

# Record our start time
time_start = time.time()


def record_read_after(avatar, message, **kwargs):
    """
    prints our read message
    see avatar.ui.message.py
    """
    global seq
    _, val, success = kwargs['watched_return']

    if not message.dst or 'model' in message.dst.name:
        l.debug("IGNR:  %s (%s, %s) @ %s" % (message, hex(message.address), val,
                                             hex(message.pc)))
    else:
        l.debug("READ:  %s (%s, %s) @ %s" % (message, hex(message.address), val,
                                             hex(message.pc)))
        G.MEM_LOG.write_row(
            ['READ', seq, message.address, val, message.pc, message.size,
             time.time()])
        # pprint.pprint(kwargs)
        seq += 1


def record_write_after(avatar, message, **kwargs):
    """
    prints our write message
    see avatar.ui.message.py
    """
    global seq
    _, val, success = kwargs['watched_return']
    if not message.dst or "model" in message.dst.name:
        l.debug("IGNW %s (%s,%s) @ %s" % (message, hex(message.address),
                                          message.value, hex(message.pc)))
    else:
        l.debug("WRITE %s (%s,%s) @ %s" % (message, hex(message.address),
                                           message.value, hex(message.pc)))
        G.MEM_LOG.write_row(
            ['WRITE', seq, message.address, message.value, message.pc,
             message.size, time.time()])
        # pprint.pprint(kwargs)
        seq += 1


def record_interrupt_enter(avatar, message, **kwargs):
    global seq
    # message.origin.wait()
    # isr = message.origin.protocols.interrupts.get_current_isr_num()
    isr = message.interrupt_num
    # TODO: Fill this out with something more intelligent
    G.MEM_LOG.write_row(['ENTER', seq, isr, 0, 0, 0, time.time()])
    l.warning \
        ("ENTER %s %s" % (hex(isr), message))
    seq += 1


def record_interrupt_exit(avatar, message, **kwargs):
    global seq
    # TODO: Fill this out with something more intelligent

    isr = message.interrupt_num
    G.MEM_LOG.write_row(['EXIT', seq, isr, 0, 0, 0, time.time()])
    l.warning("EXIT %s %s" % (hex(isr), message))
    seq += 1


def record_interrupt_return(avatar, message, **kwargs):
    # TODO: Actually make this work, return is different from exit
    # TODO: Fill this out with something more intelligent
    G.MEM_LOG.write_row(['EXIT', message.id, isr, 0, 0, 0, time.time()])
    l.debug("RETURN %s %s" % (hex(isr), message))


##
## Emulation hooks
##

def emulate_interrupt_enter(avatar, message, **kwargs):
    # message.origin.wait()
    print message
    # isr = message.origin.protocols.interrupts.get_current_isr_num()
    # TODO: Fill this out with something more intelligent
    G.OUTPUT_TSV.write_row(
        ['ENTER', message.id, message.interrupt_num, 0, 0, 0, time.time()])
    # l.warning("ENTER %s %s" % (hex(isr), message))
    # seq += 1


def emulate_interrupt_enter_alt(irq_num, **kwargs):
    # message.origin.wait()
    print message
    # isr = message.origin.protocols.interrupts.get_current_isr_num()
    # TODO: Fill this out with something more intelligent
    G.OUTPUT_TSV.write_row(
        ['ENTER', 0, self.irq_num, 0, 0, 0, 'Interrupter:%d' % irq_num])
    # l.warning("ENTER %s %s" % (hex(isr), message))
    # seq += 1


def emulate_interrupt_exit(avatar, message, **kwargs):
    print message
    # TODO: Fill this out with something more intelligent
    G.OUTPUT_TSV.write_row(
        ['EXIT', message.id, message.interrupt_num, 0, 0, 0, time.time()])
    l.warning("EXIT %s %s" % (hex(message.interrupt_num), message))


def emulate_read_before(avatar, message, **kwargs):
    """
    prints our read message
    see avatar.ui.message.py
    """
    print "READ BEFORE:  %s (%s)" % (message, hex(message.address))
    # mem_log.write_row(
    #     ['READ', message.id, message.address, val, message.pc, message.size])
    pprint.pprint(kwargs)


def emulate_write_before(avatar, message, **kwargs):
    """
    prints our write message
    see avatar.ui.message.py
    """
    print "WRITE BEFORE: %s (%s,%s)" % (message, hex(message.address),
                                        message.value)

    # mem_log.write_row(
    #     ['WRITE', message.id, message.address, val, message.pc, message.size])
    # pprint.pprint(kwargs)

