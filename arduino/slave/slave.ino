

//###############################

#define SLAVE_ADDRESS 1

//###############################


#include <Wire.h>
#include <avr/wdt.h>

const int P = 2;
const int N = 3;
const int LIMIT_PIN = 10;

int current_winding = 0;

#define DEBUG_PIN 13
#define DEBUG if (digitalRead(DEBUG_PIN) == HIGH)

void setup() {
  // Initialize I2C communication
  Wire.begin(SLAVE_ADDRESS);
  Wire.onReceive(receive);

  // Initialize pins
  pinMode(P, OUTPUT);
  pinMode(N, OUTPUT);
  pinMode(LIMIT_PIN, INPUT);
  pinMode(DEBUG_PIN, INPUT);
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
  // Get pin to use
  int PIN = 0;
  if (steps < 0) {
    steps *= -1;
    PIN = N;
  } else {
    PIN = P;
  }
  // Use pin
  for (int i = 0 ; i < steps ; i++) {
    if (digitalRead(LIMIT_PIN) == HIGH) continue;
    digitalWrite(PIN, HIGH);
    delayMicroseconds(uptime);
    digitalWrite(PIN, LOW);
    delayMicroseconds(downtime);
  }
}

void emptyWireBuffer() {
  while(Wire.available()) Wire.read();
}

void reboot() {
  wdt_disable();
  wdt_enable(WDTO_15MS);
  while (1) {}
}