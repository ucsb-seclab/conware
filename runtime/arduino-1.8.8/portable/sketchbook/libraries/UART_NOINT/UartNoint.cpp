#include "UartNoint.h"

UartNoint::UartNoint() {
  UART->UART_IDR = UART_IDR_TXRDY;
}

void UartNoint::write(byte c) {
  // Wait for UART controller
  while ((UART->UART_SR & UART_SR_TXRDY) != UART_SR_TXRDY) ; // wait
  UART->UART_THR = c;
}