#include <Servo.h>

Servo gate;
int greenPin = 9;   // change as wiring
int redPin = 10;
int servoPin = 6;

void setup(){
  Serial.begin(115200);
  gate.attach(servoPin);
  pinMode(greenPin, OUTPUT);
  pinMode(redPin, OUTPUT);
  digitalWrite(greenPin, LOW);
  digitalWrite(redPin, LOW);
  gate.write(0); // closed
}

void loop(){
  if (Serial.available()){
    String cmd = Serial.readStringUntil('\n');
    cmd.trim();
    if (cmd == "GREEN"){
      digitalWrite(redPin, LOW);
      digitalWrite(greenPin, HIGH);
      gate.write(90); // open angle  adjust as needed
      delay(3000); // keep open 3s
      gate.write(0); // close
      digitalWrite(greenPin, LOW);
      Serial.println("OK_GREEN");
    } else if (cmd == "RED"){
      digitalWrite(greenPin, LOW);
      digitalWrite(redPin, HIGH);
      delay(1500);
      digitalWrite(redPin, LOW);
      Serial.println("OK_RED");
    } else {
      // ignore
    }
  }
}
