#include <Servo.h>

#define NAME "OVI-MK1"

Servo myservo;

const int Ps[] = {2, 4, 6};
const int nPs = sizeof(Ps) / sizeof(Ps[0]);

const int Ns[] = {3, 5, 7};
const int nNs = sizeof(Ns) / sizeof(Ns[0]);

const int SERVO_PIN = 9;

#define ASSIGN = buffer; buffer = ""
#define SERVO_ENGAGE 100

void setup() {
  // Servo
  myservo.attach(SERVO_PIN);

  // Ps
  for (int i=0 ; i < nPs ; i++)
    pinMode(Ps[i], OUTPUT);

  // Ns
  for (int i=0 ; i < nNs ; i++)
    pinMode(Ns[i], OUTPUT);

  // Serial
  Serial.begin(2000000);
}

void loop() {
start:
  // Reset pins
  for (int i=0 ; i < nPs ; i++)
    digitalWrite(Ps[i], LOW);
  for (int i=0 ; i < nNs ; i++)
    digitalWrite(Ns[i], LOW);

  // Wait to receive serial data
  while (!Serial.available()) {}

  // Get name
  char c = Serial.read();
  if (c == 'w') {
    Serial.println(NAME);
    goto start;  
  }

  // Check start byte
  if (c != '>') goto start;

  // Variables
  int rot_step = 0, up_step = 0, ext_step = 0, serv_step = 0;
  unsigned long rot_up = 0, rot_down = 0, up_up = 0, up_down = 0, ext_up = 0, ext_down = 0, serv_up = 0, serv_down = 0;
  bool got_rot_step = false, got_rot_up = false, got_rot_down = false, got_up_step = false, got_up_up = false, got_up_down = false, got_ext_step = false, got_ext_up = false, got_ext_down = false, got_serv_step = false, got_serv_up = false, got_serv_down = false;
  bool skipping_rot = false, skipping_up = false, skipping_ext = false, skipping_serv = false;
  String buffer;

  // Read next char
  c = Serial.read();

  // Loop
  while (Serial.available()) {
    if (c == ':' || c == '<') {
      if (!got_rot_step && !skipping_rot) {
        rot_step = buffer.toInt();
        buffer = "";
        got_rot_step = true;
      } else if (!got_rot_up && !skipping_rot) {
        rot_up = buffer.toInt();
        buffer = "";
        got_rot_up = true;
      } else if (!got_rot_down && !skipping_rot) {
        rot_down = buffer.toInt();
        buffer = "";
        got_rot_down = true;
      } else if (!got_up_step && !skipping_up) {
        up_step = buffer.toInt();
        buffer = "";
        got_up_step = true;
      } else if (!got_up_up && !skipping_up) {
        up_up = buffer.toInt();
        buffer = "";
        got_up_up = true;
      } else if (!got_up_down && !skipping_up) {
        up_down = buffer.toInt();
        buffer = "";
        got_up_down = true;
      } else if (!got_ext_step && !skipping_ext) {
        ext_step = buffer.toInt();
        buffer = "";
        got_ext_step = true;
      } else if (!got_ext_up && !skipping_ext) {
        ext_up = buffer.toInt();
        buffer = "";
        got_ext_up = true;
      } else if (!got_ext_down && !skipping_ext) {
        ext_down = buffer.toInt();
        buffer = "";
        got_ext_down = true;
      } else if (!got_serv_step && !skipping_serv) {
        serv_step = buffer.toInt();
        buffer = "";
        got_serv_step = true;
      } else if (!got_serv_up && !skipping_serv) {
        serv_up = buffer.toInt();
        buffer = "";
        got_serv_up = true;
      } else if (!got_serv_down && !skipping_serv) {
        serv_down = buffer.toInt();
        buffer = "";
        got_serv_down = true;
      }
    } else {
      buffer += c;
    }

    c = Serial.read();
  }

  Serial.println("ROT");
  Serial.println(rot_step);
  Serial.println(rot_up);
  Serial.println(rot_down);
  Serial.println("");

  Serial.println("UP");
  Serial.println(up_step);
  Serial.println(up_up);
  Serial.println(up_down);
  Serial.println("");

  Serial.println("EXT");
  Serial.println(ext_step);
  Serial.println(ext_up);
  Serial.println(ext_down);
  Serial.println("");

  Serial.println("SERV");
  Serial.println(serv_step);
  Serial.println(serv_up);
  Serial.println(serv_down);
  Serial.println("");

  // Execute movements
  // Servo
  myservo.write((serv_step + 1) * SERVO_ENGAGE / 2);
  // Everything else
  unsigned long t = micros();
  unsigned long t_rot = t, t_up = t, t_ext = t;
  int pin_rot, pin_up, pin_ext;
  
  if (rot_step >= 0) pin_rot = Ps[0];
  else pin_rot = Ns[0];
  rot_step = abs(rot_step);
  
  if (up_step >= 0) pin_up = Ps[1];
  else pin_up = Ns[1];
  up_step = abs(up_step);
  
  if (ext_step >= 0) pin_ext = Ps[2];
  else pin_ext = Ns[2];
  ext_step = abs(ext_step);

  bool on_rot = false, on_up = false, on_ext = false;
  while (rot_step != 0 || up_step != 0 || ext_step != 0) {
    if (rot_step != 0  &&  ((on_rot && micros() - t_rot >= rot_up)  ||  (!on_rot && micros() - t_rot >= rot_down))) {
      t_rot = micros();
      if (on_rot) digitalWrite(pin_rot,  HIGH);
      else {
        digitalWrite(pin_rot, LOW);
        rot_step--;
        }
      on_rot = !on_rot;
      
    }

    if (up_step != 0  &&  ((on_up && micros() - t_up >= up_up)  ||  (!on_up && micros() - t_up >= up_down))) {
      t_up = micros();
      if (on_up) digitalWrite(pin_up,  HIGH);
      else {
        digitalWrite(pin_up, LOW);
        up_step--;
        }
      on_up = !on_up;
    }

    if (ext_step != 0  &&  ((on_ext && micros() - t_ext >= ext_up)  ||  (!on_ext && micros() - t_ext >= ext_down))) {
      t_ext = micros();
      if (on_ext) digitalWrite(pin_ext,  HIGH);
      else {
        digitalWrite(pin_ext, LOW);
        ext_step--;
        }
      on_ext = !on_ext;
    }
  }
}

void emptySerialBuffer() {
  while (Serial.available()) Serial.read();
}
