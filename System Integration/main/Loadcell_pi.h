#ifndef LOADCELL_PI_H
#define LOADCELL_PI_H

#include <Arduino.h>

#define LOADCELL_ACTION_STOP 0
#define LOADCELL_ACTION_DOWN 1
#define LOADCELL_ACTION_UP 2

void LoadcellPi_Init();

int LoadcellPi_GetApproachAction();
bool LoadcellPi_ShouldLowerForUnscrew();
bool LoadcellPi_ShouldKeepDrilling();
bool LoadcellPi_Tare();

#endif
