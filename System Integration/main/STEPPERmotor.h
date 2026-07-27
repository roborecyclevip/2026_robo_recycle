#ifndef STEPPERMOTOR_H
#define STEPPERMOTOR_H

#include <Arduino.h>


/**
 * @brief Initialize stepper motor drivers.
 */
void STEPPERmotor_Init();

/**
 * @brief Home X axis using endstop.
 */
void Stepper_HomeX();

/**
 * @brief Home Y axis using endstop.
 */
void Stepper_HomeY();

/**
 * @brief Home Z axis using endstop.
 */
void Stepper_HomeZ();

/**
 * @brief Home all axes.
 */
void Stepper_HomeAll();

/**
 * @brief Move steppers to specified coordinates in mm.
 * @param x_mm Target X position (mm).
 * @param y_mm Target Y position (mm).
 * @param z_mm Target Z position (mm).
 */
void Stepper_MoveTo(float x_mm, float y_mm, float z_mm);

/**
 * @brief Send exactly one step pulse to an axis.
 * @param axis Axis name: 'X', 'Y', or 'Z'.
 * @param direction Logical coordinate direction: +1 or -1.
 * @return true when the pulse was sent, false for invalid arguments.
 */
bool Stepper_Pulse(char axis, int direction);

/**
 * @brief Return the controller's current logical gantry position.
 */
void Stepper_GetPosition(float &x_mm, float &y_mm, float &z_mm);

#endif
