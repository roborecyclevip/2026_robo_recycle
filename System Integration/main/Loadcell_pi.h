#ifndef LOADCELL_PI_H
#define LOADCELL_PI_H

#include <Arduino.h>

void LoadcellPi_Init();

bool LoadcellPi_IsContact();
bool LoadcellPi_ShouldLowerForUnscrew();
bool LoadcellPi_ShouldKeepDrilling();
bool LoadcellPi_Tare();

#endif
