#include <AccelStepper.h>

#define MOTOR_INTERFACE_TYPE AccelStepper::DRIVER

// Pins for X axis stepper
#define X_STEP_PIN 3
#define X_DIR_PIN 6

// Endstop pin
#define X_ENDSTOP_PIN 11

AccelStepper stepperX(MOTOR_INTERFACE_TYPE, X_STEP_PIN, X_DIR_PIN);

void homeX() {
  const int homingSpeed = 200;    // steps/sec for homing
  const int backOffSteps = 50;    // steps to back off after hitting endstop

  stepperX.setMaxSpeed(homingSpeed);
  stepperX.setAcceleration(50);

  Serial.println("Homing started...");

  // Move toward endstop (assume negative direction)
  stepperX.moveTo(100000);

  // Move until endstop triggered
  while (digitalRead(X_ENDSTOP_PIN) != LOW) {
    stepperX.run();
  }

  stepperX.stop();

  // Back off a little
  stepperX.moveTo(stepperX.currentPosition() + backOffSteps);
  while (stepperX.distanceToGo() != 0) {
    stepperX.run();
  }

  // Set zero position
  stepperX.setCurrentPosition(0);
  Serial.println("Homing complete.");
}

void setup() {
  Serial.begin(9600);
  pinMode(X_ENDSTOP_PIN, INPUT_PULLUP);

  stepperX.setMaxSpeed(1000);
  stepperX.setAcceleration(200);

  Serial.println("Ready. Send 'HOME' to home the X axis.");
}

void loop() {
  if (Serial.available()) {
    String command = Serial.readStringUntil('\n');
    command.trim();

    if (command == "STOP") {
      stepperX.stop();
      Serial.println("Motor stopped.");
    }
    else if (command == "HOME") {
      homeX();
    }
    else if (command.charAt(0) == 'X') {
      long steps = command.substring(1).toInt();
      if (steps > 0) {
        stepperX.moveTo(stepperX.currentPosition() + steps);
        Serial.print("Moving X by ");
        Serial.print(steps);
        Serial.println(" steps.");
      }
    }
  }

  stepperX.run();
}
