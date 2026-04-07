#include "Loadcell.h"

// HX711 instance
HX711 loadcell(LOADCELL_DOUT_PIN, LOADCELL_SCK_PIN);

void Loadcell_Init() {
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
