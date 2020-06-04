// https://forum.arduino.cc/index.php?topic=449342.0
byte debug;
#include <UartNoint.h>

UartNoint uart;
void setup() {
  Serial.begin (9600);
 
  pinMode(LED_BUILTIN, OUTPUT);
  // disable UART tx int
//   UART->UART_IDR = UART_IDR_TXRDY;
    uart = UartNoint();
  debug = 'A';
}

void loop() {
  // put your main code here, to run repeatedly:

//   digitalWrite(LED_BUILTIN, HIGH);

  // Wait for UART controller
//   while ((UART->UART_SR & UART_SR_TXRDY) != UART_SR_TXRDY) ; // wait
  if (debug > 'Z') {
    debug = 'A';
    uart.write('\n');
//     UART->UART_THR = '\n';
//     delay(500);
  } else {
    uart.write(debug++);
//     UART->UART_THR = debug++;
  }
//   digitalWrite(LED_BUILTIN, LOW);
}
