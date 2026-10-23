#include "Arduino.h"
#include "STEPPERmotor.h"
#include "Encoder.h"
#include <cassert>
#include <iostream>

uint64_t fakeUs = 0;
int pins[64] = {};
unsigned long stopAt = 0;
bool stopSent = false;
FakeSerial Serial;

int main() {
  Encoder_Init(); Encoder_Reset();
  for (int i=0; i<1000; ++i) Encoder_Update();
  assert(Encoder_GetPosition()==0); // polling must not invent encoder edges
  pins[25]=HIGH;
  for (int i=0; i<50; ++i) {
    pins[21]=HIGH; Encoder_Update();
    for (int j=0; j<10; ++j) Encoder_Update();
    pins[21]=LOW; Encoder_Update();
  }
  assert(Encoder_GetPosition()==100);
  fakeUs+=100000;
  assert(Encoder_GetSpeedRPM()>60 && Encoder_GetSpeedRPM()<70);
  Encoder_Reset();
  assert(Encoder_GetPosition()==0 && Encoder_GetSpeedRPM()==0);

  STEPPERmotor_Init();
  assert(!Stepper_StartZMove(NAN));
  assert(Stepper_StartZMove(20));
  assert(!Stepper_StartZMove(30)); // busy move cannot be replaced
  const auto start=fakeUs;
  while (Stepper_ZMoveBusy()) Stepper_ServiceZMove();
  float x,y,z;
  Stepper_GetPosition(x,y,z);
  assert(z<=20 && z>19.99f);
  assert(fakeUs-start>1500000 && fakeUs-start<1700000);
  assert(pins[4]==LOW); // finite movement completes the last pulse
  assert(Stepper_StartZMove(0));
  for (int i=0; i<10000; ++i) Stepper_ServiceZMove();
  Stepper_StopZMove();
  Stepper_GetPosition(x,y,z);
  assert(!Stepper_ZMoveBusy() && z>0 && z<19.99f && pins[4]==LOW);
  float stoppedZ=z;
  Stepper_ServiceZMove(); Stepper_GetPosition(x,y,z);
  assert(z==stoppedZ); // stop must preserve actual position, not target position
  assert(Stepper_StartZMove(0));
  while (Stepper_ZMoveBusy()) Stepper_ServiceZMove();
  Stepper_GetPosition(x,y,z);
  assert(z>=0 && z<.01f);
  std::cout << "Encoder and cooperative Z tests passed\n";
}
