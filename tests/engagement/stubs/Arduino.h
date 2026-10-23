#pragma once
#include <cstdint>
#include <sstream>
#include <string>
#include <cmath>
using byte = uint8_t;
#define F(s) s
#define HIGH 1
#define LOW 0
#define INPUT 0
#define OUTPUT 1
#define INPUT_PULLUP 2
#define CHANGE 3
extern uint64_t fakeUs;
extern int pins[64];
extern unsigned long stopAt;
extern bool stopSent;
inline unsigned long millis() { fakeUs += 100; return fakeUs / 1000; }
inline unsigned long micros() { fakeUs += 10; return fakeUs; }
inline void delay(unsigned long ms) { fakeUs += ms * 1000; }
inline int digitalRead(int pin) { return pins[pin]; }
inline void digitalWrite(int pin, int value) { pins[pin] = value; }
inline void pinMode(int, int) {}
inline int digitalPinToInterrupt(int pin) { return pin; }
inline void attachInterrupt(int, void (*)(), int) {}
struct FakeSerial {
  std::ostringstream output;
  unsigned int stopIndex = 0;
  int available() {
    return !stopSent && stopAt && fakeUs / 1000 >= stopAt;
  }
  char read() {
    char c = "BRAKE\n"[stopIndex++];
    if (c == '\n') stopSent = true;
    return c;
  }
  template<class T> void print(T v) { output << v; }
  void print(float v, int) { output << v; }
  template<class T> void println(T v) { output << v << '\n'; }
  void println(float v, int) { output << v << '\n'; }
};
extern FakeSerial Serial;
