#include <AccelStepper.h>
const int mmToStepsXY = 200/22;
const int mmToStepsZ = 500/20;
// Define driver mode
#define MOTOR_INTERFACE_TYPE AccelStepper::DRIVER

// Replace these with the actual pins you're using
#define STEP_PIN 3
#define DIR_PIN 6

// Create the stepper instance
AccelStepper stepper(MOTOR_INTERFACE_TYPE, STEP_PIN, DIR_PIN);

void setup() {
  stepper.setMaxSpeed(200);       // steps/second
  stepper.setAcceleration(100);   // steps/sec^2
  stepper.moveTo(-2000);            // move 200 steps forward
}

void loop() {
  stepper.run();  // Keep stepping until target reached
}
