/*-----( Import needed libraries )-----*/

#include "IRremote2.h"
#include <Servo.h>

/*-----( Declare Constants )-----*/
int receiver = 11; // pin 1 of IR receiver to Arduino digital pin 11
int IR_LED = 7;

int servoPin = 6;  // Servo pin 6

// Pin definitions
const int knockSensor = 0;         // Piezo sensor on pin 0.
const int programSwitch = 2;       // If this is high we program a new code.
const int lockMotor = 3;           // Gear motor used to turn the lock.
const int redLED = 4;              // Status LED
const int greenLED = 5;            // Status LED

int GreenLedPin_2 = 8;               // Green LED connected to digital pin 8
int RedLedPin_2 = 9;                 // Red LED connected to digital pin 9
int BlueLedPin_2 = 10;               // Blue LED connected to digital pin 10

int analogPin = 1;                 // photoresistor connected to analog pin 1

// Tuning constants.  Could be made vars and hoooked to potentiometers for soft configuration, etc.
const int threshold = 300;           // Minimum signal from the piezo to register as a knock
const int rejectValue = 25;        // If an individual knock is off by this percentage of a knock we don't unlock..
const int averageRejectValue = 15; // If the average timing of the knocks is off by this percent we don't unlock.
const int knockFadeTime = 150;     // milliseconds we allow a knock to fade before we listen for another one. (Debounce timer.)

const int maximumKnocks = 20;       // Maximum number of knocks to listen for.
const int knockComplete = 1200;     // Longest time to wait for a knock before we assume that it's finished.


/*-----( Declare objects )-----*/
IRrecv irrecv(receiver);           // create instance of 'irrecv'
decode_results results;            // create instance of 'decode_results'

Servo servo;
/*-----( Declare Variables )-----*/
int servoAngle = 0;   // servo position in degrees

// Variables.
int secretCode[maximumKnocks] = {50, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0};  // Initial setup: "Shave and a Hair Cut, two bits."
int knockReadings[maximumKnocks];   // When someone knocks this array fills with delays between knocks.
int knockSensorValue = 0;           // Last reading of the knock sensor.
int programButtonPressed = false;   // Flag so we remember the programming button setting at the end of the cycle.

int GreenVal = 0;                  // variable to store the value of reflected Green light
int RedVal = 0;                    // variable to store the value of reflected Red light
int BlueVal = 0;                   // variable to store the value of reflected Blue light

int GreenRedDifference = 0;
int GreenBlueDifference = 0;

int GreenRedLockCode = 123;        // lock value
int GreenBlueLockCode = 2;        // lock value

int sensitivity = 500;               // set sensitivity of the color sensor

String passcode = "1234";
String input = "";
int count = 0;


void setup()   /*----( SETUP: RUNS ONCE )----*/
{
  Serial.begin(9600);
  Serial.println("IR Receiver Raw Data + Button Decode Test");
  irrecv.enableIRIn(); // Start the receiver
  pinMode (IR_LED, OUTPUT);


  pinMode(redLED, OUTPUT);
  pinMode(greenLED, OUTPUT);
  pinMode(programSwitch, INPUT);

  pinMode(GreenLedPin_2, OUTPUT);    // sets the digital pin as output
  pinMode(RedLedPin_2, OUTPUT);      // sets the digital pin as output
  pinMode(BlueLedPin_2, OUTPUT);     // sets the digital pin as output}

  Serial.println("Program start.");       // but feel free to comment them out after it's working right.

  servo.attach(servoPin);                   // Servo Pin

}/*--(end setup )---*/


void loop()   /*----( LOOP: RUNS CONSTANTLY )----*/
{

  digitalWrite(greenLED, LOW);
  if (irrecv.decode(&results)) // have we received an IR signal?

  {
    //translateIR();
    //Serial.println(results.value, HEX);  //UN Comment to see raw values
    if ( results.value == 0xFFA857)
    {
      knockDetector();
      irrecv.resume(); // receive the next value
    }
    // else if ( results.value == 0xFFB04F)
    // {

    //irrecv.resume(); // receive the next value
    // }
    else if (results.value == 0xFFC23D)
    {
      colorPasscode();
      irrecv.resume(); // receive the next value
    }

    remotePasscode();
    irrecv.resume(); // receive the next value
  }
}/* --(end main loop )-- */

/*-----( Declare User-written Functions )-----*/

void remotePasscode() {
  translateIR_2();
  if (count == 4) {
    compare();
    count = 0;
    input = "";
  }
  // digitalWrite(IR_LED, HIGH);
}


void knockDetector() {
  Serial.print("Knock Detector");
  digitalWrite(greenLED, HIGH);      // Green LED on, everything is go.

  while (true) {
    // Listen for any knock at all.
    knockSensorValue = analogRead(knockSensor);

    if (digitalRead(programSwitch) == HIGH) { // is the program button pressed?
      Serial.print("Programming knock detector");
      programButtonPressed = true;          // Yes, so lets save that state
      digitalWrite(redLED, HIGH);           // and turn on the red light too so we know we're programming.
    } else {
      programButtonPressed = false;
      digitalWrite(redLED, LOW);
    }

    if (knockSensorValue >= threshold) {
      listenToSecretKnock();
      return;
    }
  }
}


void colorPasscode() {

  delay(1000);
  digitalWrite(GreenLedPin_2, HIGH);   // sets the Green LED off
  digitalWrite(RedLedPin_2, HIGH);     // sets the Red LED off
  digitalWrite(BlueLedPin_2, HIGH);    // sets the Blue LED off
  delay(1000);                       // waits for a second

  green();                      //green LED on and checks input
  red();                        // red LED on and checks input
  blue();                       // blue LED on and checks input

  difference();                 // calculates differences

  if ((abs(GreenRedLockCode - GreenRedDifference) < sensitivity) && (abs(GreenBlueLockCode - GreenBlueDifference) < sensitivity)) //compare measured color value to code value
  {
    Serial.println("Unlock");                     // unlock the box
    triggerDoorUnlock();
    digitalWrite(GreenLedPin_2, LOW);   // sets the Green LED off
    digitalWrite(RedLedPin_2, LOW);     // sets the Red LED off
    digitalWrite(BlueLedPin_2, LOW);    // sets the Blue LED off
    return;

  } else {
    digitalWrite(redLED, HIGH);
    delay(500);
    digitalWrite(redLED, LOW);
    delay(500);
    digitalWrite(redLED, HIGH);
    delay(500);
    digitalWrite(redLED, LOW);
    Serial.println("Lock");
    digitalWrite(GreenLedPin_2, LOW);   // sets the Green LED off
    digitalWrite(RedLedPin_2, LOW);     // sets the Red LED off
    digitalWrite(BlueLedPin_2, LOW);    // sets the Blue LED off
    return;
  }
  delay(2000);
}

/* -----------------------------------(Knock Functions)-------------------------------*/
// Records the timing of knocks.
void listenToSecretKnock() {
  Serial.println("knock starting");

  int i = 0;
  // First lets reset the listening array.
  for (i = 0; i < maximumKnocks; i++) {
    knockReadings[i] = 0;
  }

  int currentKnockNumber = 0;             // Incrementer for the array.
  int startTime = millis();               // Reference for when this knock started.
  int now = millis();

  digitalWrite(greenLED, LOW);            // we blink the LED for a bit as a visual indicator of the knock.
  if (programButtonPressed == true) {
    digitalWrite(redLED, LOW);                         // and the red one too if we're programming a new knock.
  }
  delay(knockFadeTime);                                 // wait for this peak to fade before we listen to the next one.
  digitalWrite(greenLED, HIGH);
  if (programButtonPressed == true) {
    digitalWrite(redLED, HIGH);
  }
  do {
    //listen for the next knock or wait for it to timeout.
    knockSensorValue = analogRead(knockSensor);
    if (knockSensorValue >= threshold) {                 //got another knock...
      //record the delay time.
      Serial.println("knock.");
      now = millis();
      knockReadings[currentKnockNumber] = now - startTime;
      currentKnockNumber ++;                             //increment the counter
      startTime = now;
      // and reset our timer for the next knock
      digitalWrite(greenLED, LOW);
      if (programButtonPressed == true) {
        digitalWrite(redLED, LOW);                       // and the red one too if we're programming a new knock.
      }
      delay(knockFadeTime);                              // again, a little delay to let the knock decay.
      digitalWrite(greenLED, HIGH);
      if (programButtonPressed == true) {
        digitalWrite(redLED, HIGH);
      }
    }

    now = millis();

    //did we timeout or run out of knocks?
  } while ((now - startTime < knockComplete) && (currentKnockNumber < maximumKnocks));

  //we've got our knock recorded, lets see if it's valid
  if (programButtonPressed == false) {          // only if we're not in progrmaing mode.
    if (validateKnock() == true) {
      triggerDoorUnlock();
    } else {
      Serial.println("Secret knock failed.");
      digitalWrite(greenLED, LOW);      // We didn't unlock, so blink the red LED as visual feedback.
      for (i = 0; i < 4; i++) {
        digitalWrite(redLED, HIGH);
        delay(100);
        digitalWrite(redLED, LOW);
        delay(100);
      }
      digitalWrite(greenLED, HIGH);
    }
  } else { // if we're in programming mode we still validate the lock, we just don't do anything with the lock
    validateKnock();
    // and we blink the green and red alternately to show that program is complete.
    Serial.println("New lock stored.");
    digitalWrite(redLED, LOW);
    digitalWrite(greenLED, HIGH);
    for (i = 0; i < 3; i++) {
      delay(100);
      digitalWrite(redLED, HIGH);
      digitalWrite(greenLED, LOW);
      delay(100);
      digitalWrite(redLED, LOW);
      digitalWrite(greenLED, HIGH);
    }
  }

}


// Runs the motor (or whatever) to unlock the door.
void triggerDoorUnlock() {
  Serial.println("Door unlocked!");
  int i = 0;

  digitalWrite(greenLED, HIGH);            // And the green LED too.

  // Blink the green LED a few times for more visual feedback.
  for (i = 0; i < 5; i++) {
    digitalWrite(greenLED, LOW);
    delay(100);
    digitalWrite(greenLED, HIGH);
    delay(100);
  }

  servo.write(90);      // Turn SG90 servo back to 90 degrees (center position)
  delay(1000);
  servo.write(0);
  delay(1000);
  servo.write(90);

  digitalWrite(greenLED, LOW);

  return;
}

// Sees if our knock matches the secret.
// returns true if it's a good knock, false if it's not.
// todo: break it into smaller functions for readability.
boolean validateKnock() {
  int i = 0;

  // simplest check first: Did we get the right number of knocks?
  int currentKnockCount = 0;
  int secretKnockCount = 0;
  int maxKnockInterval = 0;               // We use this later to normalize the times.

  for (i = 0; i < maximumKnocks; i++) {
    if (knockReadings[i] > 0) {
      currentKnockCount++;
    }
    if (secretCode[i] > 0) {          //todo: precalculate this.
      secretKnockCount++;
    }

    if (knockReadings[i] > maxKnockInterval) {  // collect normalization data while we're looping.
      maxKnockInterval = knockReadings[i];
    }
  }

  // If we're recording a new knock, save the info and get out of here.
  if (programButtonPressed == true) {
    for (i = 0; i < maximumKnocks; i++) { // normalize the times
      secretCode[i] = map(knockReadings[i], 0, maxKnockInterval, 0, 100);
    }
    // And flash the lights in the recorded pattern to let us know it's been programmed.
    digitalWrite(greenLED, LOW);
    digitalWrite(redLED, LOW);
    delay(1000);
    digitalWrite(greenLED, HIGH);
    digitalWrite(redLED, HIGH);
    delay(50);
    for (i = 0; i < maximumKnocks ; i++) {
      digitalWrite(greenLED, LOW);
      digitalWrite(redLED, LOW);
      // only turn it on if there's a delay
      if (secretCode[i] > 0) {
        delay( map(secretCode[i], 0, 100, 0, maxKnockInterval)); // Expand the time back out to what it was.  Roughly.
        digitalWrite(greenLED, HIGH);
        digitalWrite(redLED, HIGH);
      }
      delay(50);
    }
    return false;   // We don't unlock the door when we are recording a new knock.
  }

  if (currentKnockCount != secretKnockCount) {
    digitalWrite(greenLED, LOW);
    return false;
  }

  /*  Now we compare the relative intervals of our knocks, not the absolute time between them.
      (ie: if you do the same pattern slow or fast it should still open the door.)
      This makes it less picky, which while making it less secure can also make it
      less of a pain to use if you're tempo is a little slow or fast.
  */
  int totaltimeDifferences = 0;
  int timeDiff = 0;
  for (i = 0; i < maximumKnocks; i++) { // Normalize the times
    knockReadings[i] = map(knockReadings[i], 0, maxKnockInterval, 0, 100);
    timeDiff = abs(knockReadings[i] - secretCode[i]);
    if (timeDiff > rejectValue) { // Individual value too far out of whack
      return false;
    }
    totaltimeDifferences += timeDiff;
  }
  // It can also fail if the whole thing is too inaccurate.
  if (totaltimeDifferences / secretKnockCount > averageRejectValue) {
    digitalWrite(greenLED, LOW);
    return false;
  }

  return true;

}

/*------------------------------------------------------(Color Functions)--------------------------------*/

void green() {
  digitalWrite(GreenLedPin_2, LOW);    // sets the Green LED on
  delay(100);
  GreenVal = 1023 - analogRead(analogPin);    // read the input pin
  Serial.println();
  Serial.print("Green ");
  Serial.println(GreenVal);          // debug value
  delay(1000);                       // waits for a second
  digitalWrite(GreenLedPin_2, HIGH);   // sets the Green LED off
  delay(1000);                       // waits for a second
}

void red() {
  digitalWrite(RedLedPin_2, LOW);      // sets the Red LED on
  delay(100);
  RedVal = 1023 - analogRead(analogPin);    // read the input pin
  Serial.print("Red ");
  Serial.println(RedVal);            // debug value
  delay(1000);                       // waits for a second
  digitalWrite(RedLedPin_2, HIGH);     // sets the Red LED off
  delay(1000);                       // waits for a second
}

void blue() {
  digitalWrite(BlueLedPin_2, LOW);     // sets the Blue LED on
  delay(100);
  BlueVal = 1023 - analogRead(analogPin);    // read the input pin
  Serial.print("Blue ");
  Serial.println(BlueVal);           // debug value
  delay(1000);                       // waits for a second
  digitalWrite(BlueLedPin_2, HIGH);    // sets the Blue LED off
}

void difference() {
  GreenRedDifference = GreenVal - RedVal;
  Serial.print("Green-Red Difference ");
  Serial.println(GreenRedDifference);           // debug value

  GreenBlueDifference = GreenVal - BlueVal;
  Serial.print("Green-Blue Difference ");
  Serial.println(GreenBlueDifference);          // debug value
}


/*------------------------------------------------------(Translate)------------------------------------*/

void translateIR() // takes action based on IR code received

// describing Car MP3 IR codes

{

  switch (results.value)

  {

    case 0xFFA25D:
      Serial.println(" CH-            ");
      break;

    case 0xFF629D:
      Serial.println(" CH             ");
      break;

    case 0xFFE21D:
      Serial.println(" CH+            ");
      break;

    case 0xFF22DD:
      Serial.println(" PREV           ");
      break;

    case 0xFF02FD:
      Serial.println(" NEXT           ");
      break;

    case 0xFFC23D:
      Serial.println(" PLAY/PAUSE     ");
      break;

    case 0xFFE01F:
      Serial.println(" VOL-           ");
      break;

    case 0xFFA857:
      Serial.println(" VOL+           ");

      break;

    case 0xFF906F:
      Serial.println(" EQ             ");
      break;

    case 0xFF6897:
      Serial.println(" 0              ");
      break;

    case 0xFF9867:
      Serial.println(" 100+           ");
      break;

    case 0xFFB04F:
      Serial.println(" 200+           ");
      break;

    case 0xFF30CF:
      Serial.println(" 1              ");
      break;

    case 0xFF18E7:
      Serial.println(" 2              ");
      break;

    case 0xFF7A85:
      Serial.println(" 3              ");
      break;

    case 0xFF10EF:
      Serial.println(" 4              ");
      break;

    case 0xFF38C7:
      Serial.println(" 5              ");
      break;

    case 0xFF5AA5:
      Serial.println(" 6              ");
      break;

    case 0xFF42BD:
      Serial.println(" 7              ");
      break;

    case 0xFF4AB5:
      Serial.println(" 8              ");
      break;

    case 0xFF52AD:
      Serial.println(" 9              ");
      break;

    default:
      Serial.println(" other button   ");

  }

  delay(500);


} //END translateIR

void translateIR_2() // takes action based on IR code received

// describing Car MP3 IR codes

{

  switch (results.value)

  {

    case 0xFFA25D:
      Serial.println(" CH-            ");
      input += "CH-";
      count++;
      //      digitalWrite(IR_LED, HIGH);
      //      digitalWrite(IR_LED, LOW);
      break;

    case 0xFF629D:
      Serial.println(" CH             ");
      input += "CH";
      count++;
      //      digitalWrite(IR_LED, LOW);
      //      digitalWrite(IR_LED, HIGH);
      break;

    case 0xFFE21D:
      Serial.println(" CH+            ");
      input += "CH+";
      count++;
      //      digitalWrite(IR_LED, LOW);
      //      digitalWrite(IR_LED, HIGH);
      break;

    case 0xFF22DD:
      Serial.println(" PREV           ");
      input += "PREV";
      count++;
      //      digitalWrite(IR_LED, LOW);
      //      digitalWrite(IR_LED, HIGH);
      break;

    case 0xFF02FD:
      Serial.println(" NEXT           ");
      input += "NEXT";
      count++;
      //      digitalWrite(IR_LED, LOW);
      //      digitalWrite(IR_LED, HIGH);
      break;

    case 0xFFC23D:
      Serial.println(" PLAY/PAUSE     ");
      //      input += "PLAY/PAUSE";
      //      count++;
      //      digitalWrite(IR_LED, LOW);
      //      digitalWrite(IR_LED, HIGH);
      break;

    case 0xFFE01F:
      Serial.println(" VOL-           ");
      input += "VOL-";
      count++;
      //      digitalWrite(IR_LED, LOW);
      //      digitalWrite(IR_LED, HIGH);
      break;

    case 0xFFA857:
      Serial.println(" VOL+           ");
      //      input += "VOL+";
      //      count++;
      //      digitalWrite(IR_LED, LOW);
      //      digitalWrite(IR_LED, HIGH);
      break;

    case 0xFF906F:
      Serial.println(" EQ             ");
      input += "EQ";
      count++;
      //      digitalWrite(IR_LED, LOW);
      //      digitalWrite(IR_LED, HIGH);
      break;

    case 0xFF6897:
      Serial.println(" 0              ");
      input += "0";
      count++;
      digitalWrite(IR_LED, LOW);
      delay(50);
      digitalWrite(IR_LED, HIGH);
      break;

    case 0xFF9867:
      Serial.println(" 100+           ");
      input += "100+";
      count++;
      //      digitalWrite(IR_LED, LOW);
      //      digitalWrite(IR_LED, HIGH);
      break;

    case 0xFFB04F:
      Serial.println(" 200+           ");
      input += "200+";
      count++;
      //      digitalWrite(IR_LED, LOW);
      //      digitalWrite(IR_LED, HIGH);
      break;

    case 0xFF30CF:
      Serial.println(" 1              ");
      input += "1";
      count++;
      digitalWrite(IR_LED, HIGH);
      delay(50);
      digitalWrite(IR_LED, LOW);
      break;

    case 0xFF18E7:
      Serial.println(" 2              ");
      input += "2";
      count++;
      digitalWrite(IR_LED, HIGH);
      delay(50);
      digitalWrite(IR_LED, LOW);
      break;

    case 0xFF7A85:
      Serial.println(" 3              ");
      input += "3";
      count++;
      digitalWrite(IR_LED, HIGH);
      delay(50);
      digitalWrite(IR_LED, LOW);
      break;

    case 0xFF10EF:
      Serial.println(" 4              ");
      input += "4";
      count++;
      digitalWrite(IR_LED, HIGH);
      delay(50);
      digitalWrite(IR_LED, LOW);
      break;

    case 0xFF38C7:
      Serial.println(" 5              ");
      input += "5";
      count++;
      digitalWrite(IR_LED, HIGH);
      delay(50);
      digitalWrite(IR_LED, LOW);
      break;

    case 0xFF5AA5:
      Serial.println(" 6              ");
      input += "6";
      count++;
      digitalWrite(IR_LED, HIGH);
      delay(50);
      digitalWrite(IR_LED, LOW);
      break;

    case 0xFF42BD:
      Serial.println(" 7              ");
      input += "7";
      count++;
      digitalWrite(IR_LED, HIGH);
      delay(50);
      digitalWrite(IR_LED, LOW);
      break;

    case 0xFF4AB5:
      Serial.println(" 8              ");
      input += "8";
      count++;
      digitalWrite(IR_LED, HIGH);
      delay(50);
      digitalWrite(IR_LED, LOW);
      break;


    case 0xFF52AD:
      Serial.println(" 9              ");
      input += "9";
      count++;
      digitalWrite(IR_LED, HIGH);
      delay(50);
      digitalWrite(IR_LED, LOW);
      break;

    default:
      Serial.println(" other button   ");

  }

  delay(500);


} //END translateIR

void compare() {

  if (input == passcode) {
    triggerDoorUnlock();

  } else {
    Serial.println("lock");
    digitalWrite(redLED, HIGH);
    delay(100);
    digitalWrite(redLED, LOW);
    delay(100);
    return;
  }
}
