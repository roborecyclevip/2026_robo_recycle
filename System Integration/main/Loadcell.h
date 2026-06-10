#ifndef LOADCELL_H
#define LOADCELL_H
#include "HX711.h"
#include <Arduino.h>

// === CONFIG ===
#define LOADCELL_DOUT_PIN A14   // Data pin
#define LOADCELL_SCK_PIN A15  // Clock pin
#define LOADCELL_CALIBRATION_FACTOR 2280   // To be calibrated
#define LOADCELL_READING_NUMBER 5

/**
 * @brief Initialize the load cell hardware and amplifier (e.g., HX711)
 */
void Loadcell_Init();

/**
 * @brief Read current load cell value
 * @return Raw or calibrated value
 */
float Loadcell_Read();

/**
 * @brief Set current load cell reading as zero (tare)
 */
void Loadcell_Tare();

#endif