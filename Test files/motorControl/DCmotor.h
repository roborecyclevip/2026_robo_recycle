#ifndef DCMOTOR_H
#define DCMOTOR_H

// Pin definitions
const int IN1 = 41;
const int IN2 = 43;
const int ENA = 45;

// Motor function declarations
void Motor1_Forward(int Speed);
void Motor1_Backward(int Speed);
void Motor1_Brake();

#endif