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
const int threshold = 10;           // Minimum signal from the piezo to register as a knock
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
int secretCode[maximumKnocks] = {50, 25, 25, 50, 100, 50, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0};  // Initial setup: "Shave and a Hair Cut, two bits."
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

int sensitivity = 5;               // set sensitivity of the color sensor

String passcode = "1234";
String input = "";
int count = 0;


void setup()   /*----( SETUP: RUNS ONCE )----*/
{
  Serial.begin(9600);

  pinMode(redLED, OUTPUT);
  pinMode(greenLED, OUTPUT);
  pinMode(programSwitch, INPUT);

  pinMode(GreenLedPin_2, OUTPUT);    // sets the digital pin as output
  pinMode(RedLedPin_2, OUTPUT);      // sets the digital pin as output
  pinMode(BlueLedPin_2, OUTPUT);     // sets the digital pin as output}


}/*--(end setup )---*/


void loop()   /*----( LOOP: RUNS CONSTANTLY )----*/
{
  colorPasscode();
}/* --(end main loop )-- */


void colorPasscode() {

  digitalWrite(GreenLedPin_2, HIGH);   // sets the Green LED off
  digitalWrite(RedLedPin_2, HIGH);     // sets the Red LED off
  digitalWrite(BlueLedPin_2, HIGH);    // sets the Blue LED off
  delay(1000);                       // waits for a second

  green();                      //green LED on and checks input
  red();                        // red LED on and checks input
  blue();                       // blue LED on and checks input

}



/*------------------------------------------------------(Color Functions)--------------------------------*/

void green() {
  digitalWrite(GreenLedPin_2, LOW);    // sets the Green LED on
  delay(100);
  GreenVal = 1023 - analogRead(analogPin);    // read the input pin
  Serial.print("G ");
  Serial.println(GreenVal);          // debug value
  delay(1000);                       // waits for a second
  digitalWrite(GreenLedPin_2, HIGH);   // sets the Green LED off
}

void red() {
  digitalWrite(RedLedPin_2, LOW);      // sets the Red LED on
  delay(100);
  RedVal = 1023 - analogRead(analogPin);    // read the input pin
  Serial.print("R ");
  Serial.println(RedVal);            // debug value
  delay(1000);                       // waits for a second
  digitalWrite(RedLedPin_2, HIGH);     // sets the Red LED off
}

void blue() {
  digitalWrite(BlueLedPin_2, LOW);     // sets the Blue LED on
  delay(100);
  BlueVal = 1023 - analogRead(analogPin);    // read the input pin
  Serial.print("B ");
  Serial.println(BlueVal);           // debug value
  digitalWrite(BlueLedPin_2, HIGH);    // sets the Blue LED off
}

