int KEY = 2;                 // Connect Touch sensor on Digital Pin 2
int buzzPin = 30;

void setup(){
  Serial.begin(9600);
  pinMode(buzzPin, OUTPUT);
  pinMode(KEY, INPUT);       //Set touch sensor pin to input mode

  Serial.println("Test");
}

void loop(){
   if(digitalRead(KEY)==HIGH) {      //Read Touch sensor signal
        Serial.println("Touch");
        digitalWrite(buzzPin, HIGH);
        delay(1);
        digitalWrite(buzzPin, LOW);
     }

}

void buzz()
{
  digitalWrite(buzzPin, HIGH);
  delay(1);
  digitalWrite(buzzPin, LOW);
}
