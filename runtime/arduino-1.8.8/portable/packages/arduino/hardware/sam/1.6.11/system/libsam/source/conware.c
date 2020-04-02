//
// Created by cspensky on 3/13/19.
//
#include <stdio.h>
#include <stdbool.h>

#define STORAGE_SIZE 3000
#define READ 0
#define WRITE 1

unsigned int MAX_REPEATS = 0xefff;
unsigned int CURRENT_INDEX = 0;
unsigned int LAST_WRITE = 0;
// unsigned int *RECORD_TIME[STORAGE_SIZE];
void *RECORD_ADDRESS[STORAGE_SIZE];
// void *RECORD_PC[STORAGE_SIZE];
unsigned int RECORD_VALUE[STORAGE_SIZE];
bool RECORD_OPERATION[STORAGE_SIZE];
unsigned int RECORD_REPEATED[STORAGE_SIZE];

bool PRINTING = false;

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
        iprintf("%d\t%d\t%08x\t%08x\t\t0\t4\t0\t\t%d\n\r",
                RECORD_OPERATION[x],
                x,
                RECORD_ADDRESS[x],
                RECORD_VALUE[x],
                //RECORD_PC[x],
                //RECORD_TIME[x],
                RECORD_REPEATED[x]);
    }
    iprintf("CONWAREDUMP_END\n\r");
    CURRENT_INDEX = 0;
    PRINTING = false;

    // TODO: Re-enabled interrupts
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
    if (address < (void *)0x40000000 || address > (void *)(0x40000000 + 0x20000000))
        return;

    // Don't log ourselves when we are printing
    if (PRINTING)
        return;

    if (CURRENT_INDEX < STORAGE_SIZE)
    {
        // Did we already see this write and just need to update the repeat counter?

        // for (int x = LAST_WRITE; x < CURRENT_INDEX; x++)
        if (CURRENT_INDEX > LAST_WRITE)
        {
            for (int x = CURRENT_INDEX - 1; x >= LAST_WRITE && x > 0; x--)
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
                    return;
                }
            }
        }
        // TODO: Get the actual systick time.
        // RECORD_TIME[CURRENT_INDEX] = 0;
        RECORD_ADDRESS[CURRENT_INDEX] = address;
        RECORD_VALUE[CURRENT_INDEX] = value;
        RECORD_OPERATION[CURRENT_INDEX] = operation;
        // RECORD_PC[CURRENT_INDEX] = __builtin_return_address(0);
        RECORD_REPEATED[CURRENT_INDEX] = 0;

        // Keep track of our last write for optimization
        if (operation == WRITE)
        {
            LAST_WRITE = CURRENT_INDEX;
        }

        CURRENT_INDEX++;
    }
    else
    {
        conware_print_results();
    }
}

void conware_interrupt_enter(unsigned int address, unsigned int value)
{
    if (PRINTING)
        return;
    printf("int enter");
}

void conware_interrupt_exit(unsigned int address, unsigned int value)
{
    if (PRINTING)
        return;
    printf("int exit");
}
