/*
  Interrupt Pin Mapping for Common Arduino Boards:

  Board         int.0   int.1   int.2   int.3   int.4   int.5
  ----------------------------------------------------------
  Mega2560        2       3      21      20      19      18

*/
// Uses Encoder by Paul Stoffregen
#include <Encoder.h>

Encoder myEnc(5, 6); // Encoder pins

const int CPR = 700; // Counts per revolution of encoder

// Variables for position
long oldPosition = -999;
long newPosition = 0;

// Variables for speed calculation
unsigned long oldTime = 0;
unsigned long newTime = 0;
float speedRPM = 0.0;  // Speed in revolutions per minute

// Direction tracking
int direction = 0; // +1 = forward, -1 = backward, 0 = stopped

void setup() {
  Serial.begin(9600);
  Serial.println("Encoder with speed and direction");
  oldPosition = myEnc.read();
  oldTime = millis();
}

void loop() {
  newPosition = myEnc.read();
  newTime = millis();

  // Calculate direction
  long deltaPosition = newPosition - oldPosition;
  if (deltaPosition > 0) direction = 1;
  else if (deltaPosition < 0) direction = -1;
  else direction = 0;

  // Calculate speed every 100ms (adjustable)
  if (newTime - oldTime >= 100) {
    // deltaPosition could be positive or negative, so use absolute value for speed
    long deltaCounts = newPosition - oldPosition;

    // Calculate revolutions in this time window
    float deltaRevs = (float)deltaCounts / CPR;

    // Calculate time elapsed in minutes
    float deltaTimeMinutes = (newTime - oldTime) / 60000.0;

    // Calculate speed in RPM
    speedRPM = deltaRevs / deltaTimeMinutes;

    // Output the data
    Serial.print("Position: ");
    Serial.print(newPosition);
    Serial.print(" | Direction: ");
    if (direction == 1) Serial.print("Forward");
    else if (direction == -1) Serial.print("Backward");
    else Serial.print("Stopped");

    Serial.print(" | Speed (RPM): ");
    Serial.println(speedRPM);

    // Update old values for next measurement
    oldPosition = newPosition;
    oldTime = newTime;
  }
}
