//
// Created by cspensky on 3/13/19.
//
#include <stdio.h>
#include <stdbool.h>

#define STORAGE_SIZE 2000
#define READ 0
#define WRITE 1

unsigned int CURRENT_INDEX = 0;
int * RECORD_TIME[STORAGE_SIZE];
void * RECORD_ADDRESS[STORAGE_SIZE];
void * RECORD_PC[STORAGE_SIZE];
unsigned int RECORD_VALUE[STORAGE_SIZE];
bool RECORD_OPERATION[STORAGE_SIZE];

bool PRINTING = false;


void conware_print_results() {
    PRINTING = true;
    int x = 0;

    iprintf("CONWAREDUMP_START\n\r");
    for (;x < STORAGE_SIZE;x++) {
//        iprintf("%d\t%d\t%d\t%08X\t%08x\n\r", x, RECORD_TIME[x], RECORD_OPERATION[x], RECORD_ADDRESS[x], RECORD_VALUE[x]);
        //format: ['Operation', 'Seqn', 'Address', 'Value', 'Value (Model)', 'PC', 'Size', 'Timestamp', 'Model']
        iprintf("%d\t%d\t%08x\t%08X\t\t%p\t4\t%d\t\n\r",
                RECORD_OPERATION[x],
                x,
                RECORD_ADDRESS[x],
                RECORD_VALUE[x],
                RECORD_PC[x],
                RECORD_TIME[x]);
    }
    iprintf("CONWAREDUMP_END\n\r");
    CURRENT_INDEX = 0;
    PRINTING = false;
}

void conware_log(void * address, unsigned int value, unsigned int operation) {
    // Only instrument MMIO
    if (address < (void *)0x40000000 || address > (void *)(0x40000000+0x20000000))
        return;

    // Don't stop on ourselves when we are printing
    if (PRINTING)
        return;

    if (CURRENT_INDEX < STORAGE_SIZE) {
        // TODO: Get the actual systick time.
        RECORD_TIME[CURRENT_INDEX] = 0;
        RECORD_ADDRESS[CURRENT_INDEX] = address;
        RECORD_VALUE[CURRENT_INDEX] = value;
        RECORD_OPERATION[CURRENT_INDEX] = operation;
        RECORD_PC[CURRENT_INDEX] = __builtin_return_address(0);
        CURRENT_INDEX++;
    } else {
        conware_print_results();
    }

}

void conware_interrupt_enter(unsigned int address, unsigned int value) {
    if (PRINTING)
        return;
    printf("int enter");
}

void conware_interrupt_exit(unsigned int address, unsigned int value) {
    if (PRINTING)
        return;
    printf("int exit");
}
