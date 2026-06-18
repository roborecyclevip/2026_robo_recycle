#include "Loadcell.h"

template <typename T>
auto makeLoadcell(int) -> decltype(T(), (HX711*)0) {
  static T instance;
  return &instance;
}

template <typename T>
T* makeLoadcell(...) {
  static T instance(LOADCELL_DOUT_PIN, LOADCELL_SCK_PIN);
  return &instance;
}

template <typename T>
auto initLoadcell(T& instance, int) -> decltype(instance.begin(LOADCELL_DOUT_PIN, LOADCELL_SCK_PIN), void()) {
  instance.begin(LOADCELL_DOUT_PIN, LOADCELL_SCK_PIN);
}

template <typename T>
void initLoadcell(T&, ...) {}

// HX711 instance
HX711& loadcell = *makeLoadcell<HX711>(0);

void Loadcell_Init() {
  initLoadcell(loadcell, 0);

  // // Wait for the chip to be ready
  // while (!scale.is_ready()) {
  //   Serial.println("Waiting for load cell to be ready...");
  //   delay(100);
  // }

  // Set the calibration factor
  loadcell.set_scale(LOADCELL_CALIBRATION_FACTOR);

  // Tare the scale to zero
  loadcell.tare();

  Serial.println("Load cell initialized and tared");
}

float Loadcell_Read() {
  return loadcell.read_average(LOADCELL_READING_NUMBER);  // Get average of LOADCELL_READING_NUMBER of readings, raw numbers
}

void Loadcell_Tare() {
  loadcell.tare();
}
