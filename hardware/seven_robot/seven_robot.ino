// Seven reference serial embodiment firmware (Arduino Uno-compatible).
#include <Servo.h>

const int LED_PIN = LED_BUILTIN;
const int BUZZER_PIN = 8;
const int SERVO_PIN = 9;
Servo sevenServo;

void ack(const String &command) { Serial.println("ACK " + command); }
void reject(const String &reason) { Serial.println("ERR " + reason); }

void setup() {
  pinMode(LED_PIN, OUTPUT);
  pinMode(BUZZER_PIN, OUTPUT);
  sevenServo.attach(SERVO_PIN);
  sevenServo.write(90);
  Serial.begin(9600);
  Serial.setTimeout(2000);
  Serial.println("READY SEVEN_ROBOT_V1");
}

void loop() {
  if (!Serial.available()) return;
  String line = Serial.readStringUntil('\n');
  line.trim();
  if (line == "LED_ON") { digitalWrite(LED_PIN, HIGH); ack(line); }
  else if (line == "LED_OFF") { digitalWrite(LED_PIN, LOW); ack(line); }
  else if (line.startsWith("LED_BLINK ")) {
    int count = constrain(line.substring(10).toInt(), 1, 100);
    for (int i = 0; i < count; i++) { digitalWrite(LED_PIN, HIGH); delay(120); digitalWrite(LED_PIN, LOW); delay(120); }
    ack("LED_BLINK " + String(count));
  }
  else if (line.startsWith("SERVO ")) {
    int angle = constrain(line.substring(6).toInt(), 0, 180);
    sevenServo.write(angle); ack("SERVO " + String(angle));
  }
  else if (line == "SCAN") {
    for (int angle = 20; angle <= 160; angle += 10) { sevenServo.write(angle); delay(40); }
    sevenServo.write(90); ack(line);
  }
  else if (line == "BUZZER" || line == "ALERT") { tone(BUZZER_PIN, 880, 300); ack(line); }
  else if (line == "CELEBRATE") { tone(BUZZER_PIN, 1200, 180); digitalWrite(LED_PIN, HIGH); delay(200); digitalWrite(LED_PIN, LOW); ack(line); }
  else if (line == "IDLE_BREATHE") { digitalWrite(LED_PIN, HIGH); delay(500); digitalWrite(LED_PIN, LOW); ack(line); }
  else if (line.startsWith("MOTOR_FWD ") || line == "MOTOR_STOP") { reject("MOTOR_DRIVER_NOT_CONFIGURED"); }
  else reject("UNKNOWN_COMMAND");
}
