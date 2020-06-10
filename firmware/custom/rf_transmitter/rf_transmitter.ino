//TRANSMITTER

// RadioHead - Version: Latest 
#include <RH_ASK.h>
// SPI - Version: Latest
// Not actualy used but needed to compile 
#include <SPI.h>

RH_ASK driver;

void setup()
{
    Serial.begin(9600);
    if (!driver.init())
         Serial.println("init failed");
}

void loop()
{
    Serial.print("Sending. ");
    const char *msg = "Hello World!";
    driver.send((uint8_t *)msg, strlen(msg));
    driver.waitPacketSent();
    delay(1000);
}
