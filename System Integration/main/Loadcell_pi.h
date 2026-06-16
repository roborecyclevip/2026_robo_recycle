#ifndef LOADCELL_PI_H
#define LOADCELL_PI_H

#include <Arduino.h>

#define LOADCELL_ACTION_STOP 0
#define LOADCELL_ACTION_DOWN 1
#define LOADCELL_ACTION_UP 2

#define ALIGNMENT_ACTION_DONE 0
#define ALIGNMENT_ACTION_FORWARD 1
#define ALIGNMENT_ACTION_BACKWARD 2
#define ALIGNMENT_ACTION_LEFT 3
#define ALIGNMENT_ACTION_RIGHT 4

void LoadcellPi_Init();

int LoadcellPi_GetApproachAction();
int LoadcellPi_GetAlignmentAction();
bool LoadcellPi_ShouldLowerForUnscrew();
bool LoadcellPi_ShouldKeepDrilling();
bool LoadcellPi_DidScrewDrop();
bool LoadcellPi_ShouldTryAnotherUnscrewPass();
bool LoadcellPi_Tare();

#endif
