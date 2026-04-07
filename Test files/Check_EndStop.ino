#define ENDSTOP_PIN 9

void setup() {
  Serial.begin(9600);
  pinMode(ENDSTOP_PIN, INPUT_PULLUP);  // Enable internal pull-up resistor
}

void loop() {
  int state = digitalRead(ENDSTOP_PIN);
  
  if (state == LOW) {
    Serial.println("ENDSTOP CLOSED (Pressed)");
  } else {
    Serial.println("ENDSTOP OPEN");
  }

  delay(5000);  // Half second delay to avoid flooding serial
}