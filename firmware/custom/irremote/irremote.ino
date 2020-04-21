#include <IRremote2.h>

int RECV_PIN = 11;
int RELAY_PIN = 4;

IRrecv irrecv(RECV_PIN);
decode_results results;

void setup() {
  // put your setup code here, to run once:
  pinMode(RELAY_PIN, OUTPUT);
  pinMode(13, OUTPUT);
  Serial.begin(9600);
  irrecv.enableIRIn();

}


void loop() {
  // put your main code here, to run repeatedly:
  if (irrecv.decode(&results)) {
    Serial.println(results.value, HEX);
     digitalWrite(RELAY_PIN, HIGH);
     delay(100);
     digitalWrite(RELAY_PIN, LOW);
    irrecv.resume();

  }

}
