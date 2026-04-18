#include "SerialConfig.h"

#define ENDSTOP_PIN 9

void setup() {
  Serial.begin(SERIAL_BAUD_RATE);
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
