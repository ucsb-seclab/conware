//RECEIVER

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
  Serial.println("Waiting for data\n");
}

void loop()
{
  uint8_t buf[12];
  uint8_t buflen = sizeof(buf);
  if (driver.recv(buf, &buflen))
  {
    int i;
    Serial.print("Message: ");
    Serial.println((char*)buf);
  }
}
