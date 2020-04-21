//
// Created by cspensky on 3/13/19.
//
#include <stdio.h>
#include <stdbool.h>
#include <stdint.h>
#include <sam3.h>

#define STORAGE_SIZE 2000
#define READ 0
#define WRITE 1
#define INTERRUPT 2

unsigned int MAX_REPEATS = 0xefff;
unsigned int CURRENT_INDEX = 0;
unsigned int LAST_WRITE = 0;
// unsigned int *RECORD_TIME[STORAGE_SIZE];
void *RECORD_ADDRESS[STORAGE_SIZE];
void *RECORD_PC[STORAGE_SIZE];
unsigned char RECORD_OPERATION[STORAGE_SIZE];
unsigned int RECORD_VALUE[STORAGE_SIZE];
unsigned int RECORD_REPEATED[STORAGE_SIZE];

bool PRINTING = false;

static void conware_common_log(void *address, unsigned int value, unsigned int operation);

inline uint32_t saveIRQState(void)
{
    uint32_t pmask = __get_PRIMASK() & 1;
    __set_PRIMASK(1);
    return pmask;
}

inline void restoreIRQState(uint32_t pmask)
{
    __set_PRIMASK(pmask);
}

/**
 * Print the results out over UART (or whatever the default printf is)
 */
void conware_print_results()
{
    PRINTING = true;
    int x = 0;

    // TODO: Disable interrupts

    iprintf("CONWAREDUMP_START\n\r");
    for (; x < STORAGE_SIZE; x++)
    {
        //        iprintf("%d\t%d\t%d\t%08X\t%08x\n\r", x, RECORD_TIME[x], RECORD_OPERATION[x], RECORD_ADDRESS[x], RECORD_VALUE[x]);
        //format: ['Operation', 'Seqn', 'Address', 'Value', 'Value (Model)', 'PC', 'Size', 'Timestamp', 'Model']
        iprintf("%d\t%d\t%08p\t%08x\t\t%08p\t4\t0\t\t%d\n\r",
                RECORD_OPERATION[x],
                x,
                RECORD_ADDRESS[x],
                RECORD_VALUE[x],
                RECORD_PC[x],
                //RECORD_TIME[x],
                RECORD_REPEATED[x]);
    }
    iprintf("CONWAREDUMP_END\n\r");
    CURRENT_INDEX = 0;
    PRINTING = false;

    // TODO: Re-enabled interrupts
}

static void conware_common_log(void *address, unsigned int value, unsigned int operation)
{
    bool print_results = CURRENT_INDEX >= STORAGE_SIZE;
    if (print_results)
    {
        conware_print_results();
    }
    // log is full
    if (CURRENT_INDEX >= STORAGE_SIZE)
    {
        return;
    }

    // Disable interrupts
    uint32_t irq_state = saveIRQState();
    __disable_irq();

    // if this is an interrupt?
    if (operation == INTERRUPT)
    {
        int last_entry_idx = CURRENT_INDEX - 1;
        bool newE = true;
        if (last_entry_idx >= 0)
        {
            if (RECORD_ADDRESS[last_entry_idx] == address &&
                RECORD_OPERATION[last_entry_idx] == operation)
            {
                RECORD_REPEATED[last_entry_idx]++;
                newE = false;
            }
        }

        if (newE)
        {
            RECORD_ADDRESS[CURRENT_INDEX] = address;
            RECORD_VALUE[CURRENT_INDEX] = value;
            RECORD_REPEATED[CURRENT_INDEX] = 0;
            RECORD_OPERATION[CURRENT_INDEX] = operation;
            RECORD_PC[CURRENT_INDEX] = __builtin_return_address(0);
            CURRENT_INDEX++;
        }
    }
    else
    {
        // this is not an interrupt
        // Did we already see this write and just need to update the repeat counter?

        // for (int x = LAST_WRITE; x < CURRENT_INDEX; x++)
        if (CURRENT_INDEX > LAST_WRITE && operation == READ)
        {
            for (unsigned int x = CURRENT_INDEX - 1; x >= LAST_WRITE && x > 0; x--)
            {
                if (RECORD_ADDRESS[x] == address &&
                    RECORD_VALUE[x] != value &&
                    RECORD_OPERATION[x] == operation)
                {
                    break;
                }
                if (RECORD_ADDRESS[x] == address &&
                    RECORD_VALUE[x] == value &&
                    RECORD_OPERATION[x] == operation)
                {
                    // Make sure this doesn't overflow...
                    if (RECORD_REPEATED[x] < MAX_REPEATS)
                    {
                        RECORD_REPEATED[x]++;
                    }
                    restoreIRQState(irq_state);
                    return;
                }
            }
        }
        // TODO: Get the actual systick time.
        // RECORD_TIME[CURRENT_INDEX] = 0;
        RECORD_ADDRESS[CURRENT_INDEX] = address;
        RECORD_VALUE[CURRENT_INDEX] = value;
        RECORD_OPERATION[CURRENT_INDEX] = operation;
        RECORD_PC[CURRENT_INDEX] = __builtin_return_address(0);
        RECORD_REPEATED[CURRENT_INDEX] = 0;

        // Keep track of our last write for optimization
        if (operation == WRITE)
        {
            LAST_WRITE = CURRENT_INDEX;
        }

        CURRENT_INDEX++;
    }
    restoreIRQState(irq_state);
    __enable_irq();
}

void conware_interrupt_log(unsigned intN)
{
    // Don't log ourselves when we are printing
    if (PRINTING)
        return;
    conware_common_log(0, intN, INTERRUPT);
}

/**
 *  Log read, write, and interrupt access to memory
 * 
 *  Operation:
 *      Read: 0
 *      Write: 1
 *      Interrupt: 2
 * 
 */
void conware_log(void *address, unsigned int value, unsigned int operation)
{
    // Only instrument MMIO
    if (address <= (void *)0x40000000 || address >= (void *)(0x40000000 + 0x20000000))
        return;

    // Don't log ourselves when we are printing
    if (PRINTING)
        return;

    conware_common_log(address, value, operation);
}
