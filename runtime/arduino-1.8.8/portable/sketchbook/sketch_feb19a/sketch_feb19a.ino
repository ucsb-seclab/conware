volatile bool led_status = LOW ;

void setup ()
{
    Serial.begin(9600);
  pinMode (13, OUTPUT) ;
  digitalWrite (13, LOW) ;
  NVIC_EnableIRQ (SVCall_IRQn) ;
  Serial.println("hi");
}

void test_supervisor () { asm volatile ("SVC #0\n\t" ::) ; }

void loop () { 
  delay(1000);
  test_supervisor () ; 
  }
