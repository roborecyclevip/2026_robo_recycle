#include "Encoder.h"

/*
  Interrupt Pin Mapping for Common Arduino Boards:

  Board         int.0   int.1   int.2   int.3   int.4   int.5
  ----------------------------------------------------------
  Mega2560        2       3      21      20      19      18

*/

// --- Encoder pins ---
const byte encoder0pinA = 21;//A pin -> the interrupt pin 0
const byte encoder0pinB = 25;//B pin -> the digital pin 4

// --- Encoder constants ---
const int CPR = 900; 

// --- Internal state ---
volatile long pulseCount = 0;
volatile bool direction = true;
volatile byte lastA = 0;

// --- Speed calculation ---
static long lastCount = 0;
static unsigned long lastTime = 0;
static float lastRPM = 0.0;


void Encoder_ISR() {
  byte a = digitalRead(encoder0pinA);
  byte b = digitalRead(encoder0pinB);

  // Classic 4-state quadrature decode
  if (a != lastA) {               // edge on A
    if (a == b)  pulseCount++;   // forward
    else         pulseCount--;   // backward
  }
  lastA = a;
}

void Encoder_Init() {
  pinMode(encoder0pinA, INPUT);
  pinMode(encoder0pinB, INPUT);
  attachInterrupt(digitalPinToInterrupt(encoder0pinA), Encoder_Update, CHANGE);
  lastTime = millis();
}

// void Encoder_Update() {
//   static byte lastA = 0;        // Must be static to persist between calls
//   byte a = digitalRead(encoder0pinA);
//   byte b = digitalRead(encoder0pinB);

//   // Only act on changes in Channel A
//   if (a != lastA) {
//     if (a == b) {
//       pulseCount++;             // Forward
//       direction = true;
//     } else {
//       pulseCount--;             // Backward
//       direction = false;
//     }
//   }
//   lastA = a;
// }

void Encoder_Update() {
  int stateA = digitalRead(encoder0pinA);
  if ((lastA == LOW) && (stateA == HIGH)) {
    int stateB = digitalRead(encoder0pinB);
    direction = (stateB == HIGH);
  }
  lastA = stateA;

  if (direction) pulseCount++;
  else pulseCount--;
}

long Encoder_GetPosition() {
  return pulseCount;
}

float Encoder_GetSpeedRPM() {
  unsigned long now = millis();
  unsigned long deltaTime = now - lastTime;

  if (deltaTime >= 100) { // update every 100 ms
    long count = pulseCount;
    long deltaCount = count - lastCount;

    // revolutions in this time window
    float deltaRevs = (float)deltaCount / CPR;

    // convert to minutes
    float deltaMinutes = deltaTime / 60000.0;

    // compute RPM
    lastRPM = deltaRevs / deltaMinutes;

    lastCount = count;
    lastTime = now;
  }

  return lastRPM;
}

int Encoder_GetDirection() {
  return direction ? 1 : -1;
}

void Encoder_Reset() {
  pulseCount = 0;
}