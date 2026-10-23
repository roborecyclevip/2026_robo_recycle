#ifndef SCREW_ENGAGEMENT_H
#define SCREW_ENGAGEMENT_H

#include <Arduino.h>

enum class ScrewEngagementResult { Engaged, NotEngaged, Aborted };

// X/Y locate the screw; Z is the expected engagement height / deepest position.
// Positive Z is DOWN. The approach height is Z - 20 mm.
// Signed PWM selects direction, just as in LOGDRILL. No screw-removal claim is made.
ScrewEngagementResult unscrew_screw_engagement(float x, float y, float z,
                                             int speed = 180,
                                             unsigned long finishMs = 3000);

#endif
