#include "DCmotor.h"
#include "Encoder.h"

extern const int CPR;

/*
  Motor Control Truth Table:

  IN1  IN2  ENA/ENB   Motor Behavior
  -------------------------------
   0    0     x      Brake (motor stops)
   1    1     x      Invalid / Vacant
   1    0     1      Forward at full speed
   0    1     1      Reverse at full speed
   1    0    PWM     Forward at PWM speed
   0    1    PWM     Reverse at PWM speed

  Notes:
  - IN1/IN2 control the direction.
  - ENA/ENB control the speed via PWM (0–255).
  - 'x' means don't care (can be 0 or 1).
  - The (1,1) state is typically avoided to prevent conflict in the H-bridge.
*/

// Pin definitions
const int IN1 = 41;
const int IN2 = 43;
const int ENA = 45;

void DCmotor_Init() {
  pinMode(IN1, OUTPUT);
  pinMode(IN2, OUTPUT);
  pinMode(ENA, OUTPUT);
}

void Motor_Forward(int speed) {
  digitalWrite(IN1, HIGH);
  digitalWrite(IN2, LOW);
  analogWrite(ENA, speed);
}

void Motor_Backward(int speed) {
  digitalWrite(IN1, LOW);
  digitalWrite(IN2, HIGH);
  analogWrite(ENA, speed);
}

void Motor_Brake() {
  digitalWrite(IN1, LOW);
  digitalWrite(IN2, LOW);
}

// ---------------------------------------------------------------------------
// Helper: absolute target pulse count
// ---------------------------------------------------------------------------
static long targetPulses(float degrees)
{
    // One full turn = CPR pulses
    // degrees to pulses:  degrees * CPR / 360
    return (long)(degrees * CPR / 360.0f);
}

// ---------------------------------------------------------------------------
// Motor_RotateDegrees
// ---------------------------------------------------------------------------
bool Motor_RotateDegrees(float degrees, int speed, unsigned long timeoutMs)
{
    if (speed < 0)   speed = 0;
    if (speed > 255) speed = 255;

    // -------------------------------------------------------------------
    // 1. Prepare encoder
    // -------------------------------------------------------------------
    Encoder_Reset();                     // start from zero
    long target = targetPulses(degrees); // may be negative
    long absTarget = abs(target);

    //Serial.println(target);

    // -------------------------------------------------------------------
    // 2. Start motor in the correct direction
    // -------------------------------------------------------------------
    if (degrees > 0) {
        Motor_Forward(speed);
    } else if (degrees < 0) {
        Motor_Backward(speed);
    } else {
        Motor_Brake();                  // 0 degrees to nothing to do
        return true;
    }

    // -------------------------------------------------------------------
    // 3. Wait until we reach the target (or timeout)
    // -------------------------------------------------------------------
    unsigned long start = millis();

    while (true) {
        Encoder_Update();

        long pos = abs(Encoder_GetPosition());          // current pulse count
        // ----- reached target? -----
        if (pos >= absTarget) {
          break;
        }

        // ----- timeout? -----
        if (timeoutMs && (millis() - start) >= timeoutMs) {
            Motor_Brake();
            return false;   // timed-out
        }

        // Small delay to keep the loop responsive but not hog CPU
        delay(1);
    }
    // -------------------------------------------------------------------
    // 4. Stop
    // -------------------------------------------------------------------
    Motor_Brake();
    return true;            // success
}
