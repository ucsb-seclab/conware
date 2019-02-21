void setup() {
  // put your setup code here, to run once:
  pinMode(LED_BUILTIN, OUTPUT);
//  Serial.begin(9600);/
}

void loop() {
  // put your main code here, to run repeatedly:
//  Serial.print("ON\n");/
  digitalWrite(LED_BUILTIN, HIGH);
  delay(1000);
//  Serial.print("of/f\n");
  digitalWrite(LED_BUILTIN, LOW);
  delay(500);
}
