from collections import OrderedDict


class PeripheralMemoryMap:
    def __init__(self):
        pass

    system_controller = [0x400E0000, 0x400E2600]

    peripheral_memory = OrderedDict()
    peripheral_memory['HSMCI'] = [0x40000000, 0x40004000]
    peripheral_memory['SSC'] = [0x40004000, 0x40008000]
    peripheral_memory['SPI0'] = [0x40008000, 0x4000C000]
    peripheral_memory['SPI1'] = [0x4000C000, 0x40080000]
    peripheral_memory['TC0'] = [0x40080000, 0x40084000]
    peripheral_memory['TC1'] = [0x40084000, 0x40088000]
    peripheral_memory['TC2'] = [0x40088000, 0x4008C000]
    peripheral_memory['TWI0'] = [0x4008C000, 0x40090000]
    peripheral_memory['TWI1'] = [0x40090000, 0x40094000]
    peripheral_memory['PWM'] = [0x40094000, 0x40098000]
    peripheral_memory['USART0'] = [0x40098000, 0x4009C000]
    peripheral_memory['USART1'] = [0x4009C000, 0x400A0000]
    peripheral_memory['USART2'] = [0x400A0000, 0x400A4000]
    peripheral_memory['USART3'] = [0x400A4000, 0x400A8000]
    peripheral_memory['Reserved0'] = [0x400A8000, 0x400AC000]
    peripheral_memory['UOTGHS'] = [0x400AC000, 0x400B0000]
    peripheral_memory['EMAC'] = [0x400B0000, 0x400B4000]
    peripheral_memory['CAN0'] = [0x400B4000, 0x400B8000]
    peripheral_memory['CAN1'] = [0x400B8000, 0x400BC000]
    peripheral_memory['TRNG'] = [0x400BC000, 0x400C0000]
    peripheral_memory['ADC'] = [0x400C0000, 0x400C4000]
    peripheral_memory['DMAC'] = [0x400C4000, 0x400C8000]
    peripheral_memory['DACC'] = [0x400C8000, 0x400D0000]
    peripheral_memory['Reserved1'] = [0x400D0000, 0x400E0000]
    # System controller
    peripheral_memory['SMC'] = [0x400E0000, 0x400E0200]
    peripheral_memory['SDRAM'] = [0x400E0200, 0x400E0400]
    peripheral_memory['MATRIX'] = [0x400E0400, 0x400E0600]
    peripheral_memory['PMC'] = [0x400E0600, 0x400E0800]
    peripheral_memory['UART'] = [0x400E0800, 0x400E0940]
    peripheral_memory['CHIPID'] = [0x400E0940, 0x400E0A00]
    peripheral_memory['EEFC0'] = [0x400E0A00, 0x400E0C00]
    peripheral_memory['EEFC1'] = [0x400E0C00, 0x400E0E00]
    peripheral_memory['PIOA'] = [0x400E0E00, 0x400E1000]
    peripheral_memory['PIOB'] = [0x400E1000, 0x400E1200]
    peripheral_memory['PIOC'] = [0x400E1200, 0x400E1400]
    peripheral_memory['PIOD'] = [0x400E1400, 0x400E1600]
    peripheral_memory['PIOE'] = [0x400E1600, 0x400E1800]
    peripheral_memory['PIOF'] = [0x400E1800, 0x400E1A00]
    peripheral_memory['RSTC'] = [0x400E1A00, 0x400E1A10]
    peripheral_memory['SUPC'] = [0x400E1A10, 0x400E1A30]
    peripheral_memory['RTT'] = [0x400E1A30, 0x400E1A50]
    peripheral_memory['WDT'] = [0x400E1A50, 0x400E1A60]
    peripheral_memory['RTC'] = [0x400E1A60, 0x400E1A90]
    peripheral_memory['GPBR'] = [0x400E1A90, 0x400E1AB0]
    peripheral_memory['Reserved2'] = [0x400E1AB0, 0x400E2600]
    peripheral_memory['Reserved3'] = [0x400E2600, 0x60000000]

    def get_peripheral(self, address):
        """
        Lookup a given memory address and return the peripheral that it
        belongs to.

        :param address: memory address to lookup
        :return: (peripheral name, [periphal range])
        """

        for periph in self.peripheral_memory:
            if self.peripheral_memory[periph][0] <= address < \
                    self.peripheral_memory[periph][1]:
                return periph, self.peripheral_memory[periph]

        return None

    def check_cluster(self, start_address, end_address):
        """

        :param start_address:
        :param end_address:
        :return: Name of peripheral or None if it's not a valid memory range
        """
        for periph in self.peripheral_memory:
            if start_address >= self.peripheral_memory[periph][0] and \
                            end_address < self.peripheral_memory[periph][1]:
                return periph

        return None
