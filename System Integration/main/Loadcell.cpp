#include "Loadcell.h"

// HX711 instance
HX711 loadcell(LOADCELL_DOUT_PIN, LOADCELL_SCK_PIN);

static int askApproachAction() {
  Serial.println("Type UP, DOWN, or STOP:");

  String input = "";
  while (true) {
    while (Serial.available()) {
      char c = (char)Serial.read();

      if (c == '\n' || c == '\r') {
        input.trim();
        input.toUpperCase();

        if (input == "UP") return LOADCELL_ACTION_UP;
        if (input == "DOWN") return LOADCELL_ACTION_DOWN;
        if (input == "STOP") return LOADCELL_ACTION_STOP;

        input = "";
        Serial.println("Please type UP, DOWN, or STOP:");
      } else {
        input += c;
      }
    }
  }
}

int LoadcellPi_GetApproachAction() {
  Serial.println("Approach action?");
  return askApproachAction();
}

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
