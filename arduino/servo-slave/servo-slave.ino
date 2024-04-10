#include <Servo.h>



//###############################

#define SLAVE_ADDRESS 1

//###############################


#include <Wire.h>
#include <avr/wdt.h>

Servo myservo;

const int SERVO_PIN = 2;
const int SERVO_REST = 0;
const int SERVO_ENGAGE = 90;

#define DEBUG_PIN 13
#define DEBUG if (digitalRead(DEBUG_PIN) == HIGH)

void setup() {
  // Initialize I2C communication
  Wire.begin(SLAVE_ADDRESS);
  Wire.onReceive(receive);

  // Initialize pins
  myservo.attach(SERVO_PIN);
  myservo.write(SERVO_REST);
}

void loop() {}

void receive(int bytes) {
  // Check starting byte
  char c = Wire.read();
  if (c == 'R') reboot();
  if (c != '>') {
    emptyWireBuffer();
    return;
  }

  // Read
  String buff="";
  int steps = 0;
  unsigned int uptime=0, downtime=0;
  bool gotSteps=false, gotUp=false, gotDown=false;
  while(c != '<') {
    c = Wire.read();
    if (c == ':' || c == '<') {
      if (!gotSteps) {steps = buff.toInt(); gotSteps = true;}
      else if (!gotUp) {uptime = buff.toInt(); gotUp = true;}
      else if (!gotDown) {downtime = buff.toInt(); gotDown = true;}
      else {return;}
      buff = "";
    } else {
      buff += c;
    }
  }

  // Execute movements
  if (steps > 0) myservo.write(SERVO_ENGAGE);
  if (steps < 0) myservo.write(SERVO_REST);
}

void emptyWireBuffer() {
  while(Wire.available()) Wire.read();
}

void reboot() {
  wdt_disable();
  wdt_enable(WDTO_15MS);
  while (1) {}
}