// RoboReCycle 2025
// DC Motor Basic Control

#include "DCmotor.h"


void setup() {
     pinMode(IN1, OUTPUT);
     pinMode(IN2, OUTPUT);
     pinMode(ENA, OUTPUT);
}

void loop() {
 //Motor1_Brake();
 delay(100);
 Motor1_Forward(200);
 delay(1000);
 Motor1_Brake();
 delay(100);
 Motor1_Backward(200);
 delay(1000);
}

