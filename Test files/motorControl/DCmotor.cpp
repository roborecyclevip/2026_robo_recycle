#include <Arduino.h>
#include "DCmotor.h"

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

void Motor1_Forward(int Speed)
{
    digitalWrite(IN1, HIGH);
    digitalWrite(IN2, LOW);
    analogWrite(ENA, Speed);
}

void Motor1_Backward(int Speed)
{
    digitalWrite(IN1, LOW);
    digitalWrite(IN2, HIGH);
    analogWrite(ENA, Speed);
}

void Motor1_Brake()
{
    digitalWrite(IN1, LOW);
    digitalWrite(IN2, LOW);
}