#include <Stepper.h>

#ifndef STEPPERMOTOR_H
#define STEPPERMOTOR_H

#include "MultiStepperLite.h"

// === CONFIG ===
#define STEPS_PER_MM_XY 72.2543352601  // 10000 steps / 138.4 mm
#define STEPS_PER_MM_Z 206.611570248     // 10000 steps / 48.4 mm

// === X AXIS ===
#define X_STEP_PIN 2
#define X_DIR_PIN 5
#define X_ENDSTOP_PIN 10
#define X_MOTOR_INDEX 0

// === Y AXIS ===
#define Y_STEP_PIN 3
#define Y_DIR_PIN 6
#define Y_ENDSTOP_PIN 9
#define Y_MOTOR_INDEX 1

// === Z AXIS ===
#define Z_STEP_PIN 4
#define Z_DIR_PIN 7
#define Z_ENDSTOP_PIN 11
#define Z_MOTOR_INDEX 2

// Step intervals in microseconds (derived from max speed)
#define STEP_INTERVAL_XY 10    // 100,000 steps/s = 10 µs/step
#define STEP_INTERVAL_Z 33     // 30,000 steps/s ≈ 33 µs/step
#define HOMING_STEP_INTERVAL 5000  // 200 steps/s = 5,000 µs/step

// Global stepper instance and position variables
MultiStepperLite steppers(3); // Initialize with 3 motors (X, Y, Z)
float currentX = 0.0; // Current position in mm
float currentY = 0.0;
float currentZ = 0.0;

void setDirection(int dirPin, bool forward) {
  digitalWrite(dirPin, forward ? HIGH : LOW);
}

// homeAxis
void homeAxis(uint8_t motorIndex, int dirPin, int endstopPin, const char* axisName, bool reverse) {
  Serial.print("Homing ");
  Serial.println(axisName);

  if (digitalRead(endstopPin) == LOW) {
    return;
  }

  pinMode(dirPin, OUTPUT);
  setDirection(dirPin, reverse ? true : false); // Z homes in positive direction, X/Y negative
  steppers.start_continuous(motorIndex, 200);

  while (digitalRead(endstopPin) != LOW) {
    steppers.do_tasks();
  }

  steppers.stop(motorIndex);
  while (!steppers.is_finished(motorIndex)) {
    steppers.do_tasks(); // Ensure graceful stop (step pin LOW)
  }

  // Reset position to 0
  if (motorIndex == X_MOTOR_INDEX) currentX = 0.0;
  if (motorIndex == Y_MOTOR_INDEX) currentY = 0.0;
  if (motorIndex == Z_MOTOR_INDEX) currentZ = 0.0;

  Serial.print("Homed ");
  Serial.println(axisName);
}

void STEPPERmotor_Init() {
  // Initialize endstop pins
  pinMode(X_ENDSTOP_PIN, INPUT_PULLUP);
  pinMode(Y_ENDSTOP_PIN, INPUT_PULLUP);
  pinMode(Z_ENDSTOP_PIN, INPUT_PULLUP);

  // Initialize steppers
  steppers.init_stepper(X_MOTOR_INDEX, X_STEP_PIN);
  steppers.init_stepper(Y_MOTOR_INDEX, Y_STEP_PIN);
  steppers.init_stepper(Z_MOTOR_INDEX, Z_STEP_PIN);

  // Set step intervals
  steppers.set_step_interval(X_MOTOR_INDEX, STEP_INTERVAL_XY);
  steppers.set_step_interval(Y_MOTOR_INDEX, STEP_INTERVAL_XY);
  steppers.set_step_interval(Z_MOTOR_INDEX, STEP_INTERVAL_Z);

  // Initialize direction pins
  pinMode(X_DIR_PIN, OUTPUT);
  pinMode(Y_DIR_PIN, OUTPUT);
  pinMode(Z_DIR_PIN, OUTPUT);

  // Enable time autocorrect
#if TIME_AUTOCORRECT_SUPPORT
  steppers.set_autocorrect(true);
  steppers.set_min_step_interval(X_MOTOR_INDEX, STEP_INTERVAL_XY);
  steppers.set_min_step_interval(Y_MOTOR_INDEX, STEP_INTERVAL_XY);
  steppers.set_min_step_interval(Z_MOTOR_INDEX, STEP_INTERVAL_Z);
#endif

  // Initialize positions
  currentX = 0.0;
  currentY = 0.0;
  currentZ = 0.0;
}

void Stepper_HomeX() {
  homeAxis(X_MOTOR_INDEX, X_DIR_PIN, X_ENDSTOP_PIN, "X", false);
}

void Stepper_HomeY() {
  homeAxis(Y_MOTOR_INDEX, Y_DIR_PIN, Y_ENDSTOP_PIN, "Y", false);
}

void Stepper_HomeZ() {
  homeAxis(Z_MOTOR_INDEX, Z_DIR_PIN, Z_ENDSTOP_PIN, "Z", true);
}

void Stepper_HomeAll() {
  Stepper_HomeZ();
  Stepper_HomeX();
  Stepper_HomeY();
}

void Stepper_MoveTo(float x_mm, float y_mm, float z_mm) {
  // Convert coordinates to steps
  long x_steps = (long)((x_mm - currentX) * STEPS_PER_MM_XY);
  long y_steps = (long)((y_mm - currentY) * STEPS_PER_MM_XY);
  long z_steps = (long)((z_mm - currentZ) * STEPS_PER_MM_Z);

  // Set direction based on step sign (negative steps = reverse)
  setDirection(X_DIR_PIN, x_steps >= 0); // AccelStepper used -x_steps, so reverse if positive
  setDirection(Y_DIR_PIN, y_steps >= 0); // AccelStepper used -y_steps
  setDirection(Z_DIR_PIN, z_steps <= 0); // Z direction matches steps

  // Start motors with absolute step counts
  // steppers.start_finite(1, 1000, 2500);
  // steppers.start_finite(2, 1000, 2500);
  steppers.start_finite(X_MOTOR_INDEX, 200, abs(x_steps));
  steppers.start_finite(Y_MOTOR_INDEX, 200, abs(y_steps));
  steppers.start_finite(Z_MOTOR_INDEX, 200, abs(z_steps));

  int count = 0;
  // Poll until all motors are finished
  while (!steppers.is_finished(X_MOTOR_INDEX) || 
    !steppers.is_finished(Y_MOTOR_INDEX) || 
    !steppers.is_finished(Z_MOTOR_INDEX)) {
      // if (count % 50000 == 0) {
      //   Serial.println(Loadcell_Read());
      // }


    steppers.do_tasks();
  }

  // Update current positions
  currentX = x_mm;
  currentY = y_mm;
  currentZ = z_mm;
}

#endif