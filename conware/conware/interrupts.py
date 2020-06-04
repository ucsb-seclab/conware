import logging
import sys

logger = logging.getLogger(__name__)
from threading import Thread, Event
from avatar2 import TargetStates
import time


class Interrupter(Thread):
    host = None

    def __init__(self, irq_num, host, rate=.01, count=-1):
        """

        :param irq_num: IRQ # in QEMU
        :param rate:
        """
        self.irq_num = irq_num
        self.interrupt_rate = rate
        self.host = host
        self.count = count
        self._shutdown = Event()
        logger.debug("Creating Interrupter for IRQ %d" % self.irq_num)
        Thread.__init__(self)

    def _send_irq(self):
        logger.debug("Sending IRQ %d (interval: %d s)" % (self.irq_num, self.interrupt_rate))
        # try:
        self.host.protocols.interrupts.inject_interrupt(self.irq_num)
        # except:
        #     logger.exception("Error injecting interrupt.")
        # OUTPUT_TSV.write_row(
        #     ['INTERRUPT', seq,
        #      "0x%08x" % 0,
        #      "%08x" % self.irq_num,
        #      "%08x" % 0,
        #      "0x%x" % 0,
        #      0, time.time() - time_start, "???"])

    def run(self):
        logger.info("Starting Interrupter for IRQ %d (count: %d)" % (self.irq_num, self.count))
        if not self.host:
            raise RuntimeError("Must set host first")
        ignored = False
        # self.host.protocols.interrupts.ignore_interrupt_return(
        #     self.irq_num)
        if self.count == -1:
            while not self._shutdown.is_set():
                # if not ignored:
                #     logger.info(
                #         "Ignoring interrupt returns for IRQ %d" % self.irq_num)
                #     self.host.protocols.interrupts.ignore_interrupt_return(
                #         self.irq_num)
                #     ignored = True
                self._send_irq()
                time.sleep(self.interrupt_rate)
        else:
            for x in xrange(self.count):
                self._send_irq()
                time.sleep(self.interrupt_rate)



# class StatefulInterrupter(Thread):
#     host = None
#
#     def __init__(self, irq_num, trigger, timings):
#         self.irq_num = irq_num
#         self.trigger = trigger
#         self.timings = timings
#         self.irq_enabled = Event()
#         self.interrupt_now = Event()
#         self.started = Event()
#         self._shutdown = Event()
#         logger.debug("Creating Interrupter for IRQ %d" % self.irq_num)
#         Thread.__init__(self)
#
#     def send_interrupt(self):
#         while self.interrupt_now.is_set():
#             pass
#         self.interrupt_now.set()
#
#     def run(self):
#         logger.info("Starting Stateful Interrupter for IRQ %d" % self.irq_num)
#         self.started.set()
#         if not self.host:
#             raise RuntimeError("Must set host first")
#         ignored = False
#         while not self._shutdown.is_set():
#             self.interrupt_now.wait()
#             if not ignored:
#                 logger.info(
#                     "Ignoring interrupt returns for IRQ %d" % self.irq_num)
#                 self.host.protocols.interrupts.ignore_interrupt_return(
#                     self.irq_num)
#                 ignored = True
#             logger.info("Sending IRQ %d" % self.irq_num)
#             self.host.protocols.interrupts.inject_interrupt(self.irq_num)
#             self.interrupt_now.clear()
#             """
#             while not self.irq_enabled.is_set() or self.host.state != TargetStates.RUNNING:
#                 pass
#             logger.info("Ignoring interrupt returns for IRQ %d" % self.irq_num)
#             self.host.protocols.interrupts.ignore_interrupt_return(self.irq_num)
#             t = 0
#             while not self._shutdown.is_set() and self.irq_enabled.is_set() and self.host.state == TargetStates.RUNNING:
#                 self.interrupt_now.wait()
#                 logger.info("Sending IRQ %d" % self.irq_num)
#                 self.host.protocols.interrupts.inject_interrupt(self.irq_num)
#                 self.interrupt_now.clear()
#             """
#
#
# class Interrupter(Thread):
#     host = None  # The host to be interrupted. MUST SET AT RUNTIME
#
#     # This is probably a QemuTarget
#
#     def __init__(self, peripheral, irq_num, trigger, timings, oneshot=False):
#         self.peripheral = peripheral
#         self.irq_num = irq_num
#         self.trigger = trigger
#         self.timings = timings
#         self.irq_enabled = Event()
#         self.started = Event()
#         self._shutdown = Event()
#         self.oneshot = oneshot
#         logger.debug("Creating Interrupter for IRQ %d" % self.irq_num)
#         Thread.__init__(self)
#
#     def run(self):
#         logger.info("Starting Interrupter for IRQ %d" % self.irq_num)
#         self.started.set()
#         if not self.host:
#             raise RuntimeError("Must set host first")
#         ignored = False
#         while not self._shutdown.is_set():
#             t = 0
#             while not self._shutdown.is_set() and self.irq_enabled.is_set() and self.host.state == TargetStates.RUNNING:
#                 #if not ignored:
#                 #    logger.info("Ignoring interrupt returns for IRQ %d" % self.irq_num)
#                 #    self.host.protocols.interrupts.ignore_interrupt_return(self.irq_num)
#                 #    ignored = True
#                 next_time = self.timings[t]
#                 logger.info("[%d] Sleeping for %f" % (self.irq_num, next_time))
#                 time.sleep(next_time)
#                 # DO IT
#                 logger.info("Sending IRQ %d" % self.irq_num)
#                 self.host.protocols.interrupts.inject_interrupt(self.irq_num)
#                 #emulate_interrupt_enter_alt(irq_num)
#                 self.peripheral.enter(self.irq_num)
#                 t = (t + 1) % len(self.timings)
#                 # If you had.... one shot..... one opportunity
#                 if self.oneshot:
#                     logger.warn("One shotted IRQ %d" % self.irq_num)
#                     self.irq_enabled.clear()
#     def shutdown(self):
#         self._shutdown.set()

