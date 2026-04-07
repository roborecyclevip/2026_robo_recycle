#include <AccelStepper.h>

// === CONFIG ===
#define MOTOR_INTERFACE_TYPE AccelStepper::DRIVER
#define STEPS_PER_MM_XY 9.09  // 200 steps / 22 mm
#define STEPS_PER_MM_Z 20     // 500 steps / 25 mm

// === X AXIS ===
#define X_STEP_PIN 2
#define X_DIR_PIN 5
#define X_ENDSTOP_PIN 10
AccelStepper stepperX(MOTOR_INTERFACE_TYPE, X_STEP_PIN, X_DIR_PIN);

// === Y AXIS ===
#define Y_STEP_PIN 3
#define Y_DIR_PIN 6
#define Y_ENDSTOP_PIN 9
AccelStepper stepperY(MOTOR_INTERFACE_TYPE, Y_STEP_PIN, Y_DIR_PIN);

// === Z AXIS ===
#define Z_STEP_PIN 4
#define Z_DIR_PIN 7
#define Z_ENDSTOP_PIN 11
AccelStepper stepperZ(MOTOR_INTERFACE_TYPE, Z_STEP_PIN, Z_DIR_PIN);

// === HOMING FUNCTION TEMPLATE ===
void homeAxis(AccelStepper &stepper, int endstopPin, const char* axisName) {
  const int homingSpeed = 200;

  stepper.setMaxSpeed(homingSpeed);
  stepper.setAcceleration(50);
  if (strcmp(axisName, "Z") == 0) {
    stepper.moveTo(-100000);  // Move far in negative direction
  } else {
    stepper.moveTo(100000);  // Move far in negative direction
  }
  
  Serial.print("Homing ");
  Serial.println(axisName);

  while (digitalRead(endstopPin) != LOW) {
    stepper.run();
  }

  stepper.stop();

  stepper.setCurrentPosition(0);
  Serial.print("Homed ");
  Serial.println(axisName);
}

// === INDIVIDUAL HOMING FUNCTIONS ===
void homeX() { homeAxis(stepperX, X_ENDSTOP_PIN, "X"); }
void homeY() { homeAxis(stepperY, Y_ENDSTOP_PIN, "Y"); }
void homeZ() { homeAxis(stepperZ, Z_ENDSTOP_PIN, "Z"); }

// === SETUP ===
void setup() {
  Serial.begin(9600);

  pinMode(X_ENDSTOP_PIN, INPUT_PULLUP);
  pinMode(Y_ENDSTOP_PIN, INPUT_PULLUP);
  pinMode(Z_ENDSTOP_PIN, INPUT_PULLUP);

  stepperX.setMaxSpeed(1000);
  stepperX.setAcceleration(200);

  stepperY.setMaxSpeed(1000);
  stepperY.setAcceleration(200);

  stepperZ.setMaxSpeed(1000);
  stepperZ.setAcceleration(200);

}

// === LOOP ===
void loop() {
  if (Serial.available()) {
    String command = Serial.readStringUntil('\n');
    command.trim();

    if (command == "HOMEX") {
      homeX();
    } else if (command == "HOMEY") {
      homeY();
    } else if (command == "HOMEZ") {
      homeZ();
    }

    else if (command.startsWith("XY")) {
      int commaIndex = command.indexOf(',');
      if (commaIndex > 2) {
        float x_mm = command.substring(2, commaIndex).toFloat();
        float y_mm = command.substring(commaIndex + 1).toFloat();

        long x_steps = x_mm * STEPS_PER_MM_XY;
        long y_steps = y_mm * STEPS_PER_MM_XY;

        stepperX.moveTo(-x_steps);
        stepperY.moveTo(-y_steps);

        Serial.print("Moving to X: ");
        Serial.print(x_mm);
        Serial.print(" mm, Y: ");
        Serial.print(y_mm);
        Serial.println(" mm");
      }
    }

    else if (command.startsWith("Z")) {
      float z_mm = command.substring(1).toFloat();
      long z_steps = z_mm * STEPS_PER_MM_Z;
      stepperZ.moveTo(z_steps);

      Serial.print("Moving to Z: ");
      Serial.print(z_mm);
      Serial.println(" mm");
    }
  }

  // Run all steppers
  stepperX.run();
  stepperY.run();
  stepperZ.run();
}

