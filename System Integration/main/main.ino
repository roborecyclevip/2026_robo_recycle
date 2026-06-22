#include <Arduino.h>
#include "DCmotor.h"
#include "STEPPERmotor.h"
#include "Encoder.h"
#include "Loadcell_pi.h"
#include "Loadcell.h"
#include "Current.h"

#define LOADCELL_THRESHOLD 5.0
#define LOADCELL_ENGAGEMENT_DEADBAND 10.0

#define SAFE_Z 80.0
#define SCREW_DROPOFF_X 225.0
#define SCREW_DROPOFF_Y 330.0
#define SCREW_DROPOFF_APPROACH_Y 280.0

#define STEPPER_INCREMENT 0.1
#define SCREW_ALIGNMENT_NUDGE_MM 1.0

float load_cell_reading = 0.0;
float motor_speed = 0.0;

float targetX = 0.0;
float targetY = 0.0;
float targetZ = 0.0;

// Serial command buffer
String inputString = "";
bool stringComplete = false;

void setup() {
  Serial.begin(115200);
  DCmotor_Init();
  STEPPERmotor_Init();
  Encoder_Init();
  Loadcell_Init();
  LoadcellPi_Init();

  Stepper_HomeAll();
  Serial.println(F("System Homed and Ready"));
  Serial.println(F("R2 Robot Starting..."));
  Serial.println(F("Type HELP for commands"));

  inputString.reserve(64);  // prevent memory fragmentation
}


void printHelp() {
  Serial.println(F("\n=== R2 ROBOT COMMANDS ==="));
  Serial.println(F("HOME                → Home all steppers"));
  Serial.println(F("GOTO X Y Z          → Move gantry"));
  Serial.println(F("DRILL deg [spd]     → Rotate drill (spd=0-255)"));
  Serial.println(F("UNSCREW X Y         → Manual-assisted screw flow at X,Y"));
  Serial.println(F("UNSCREWCHAIN n ...  → Run screw flow for coordinate list"));
  Serial.println(F("Alignment prompts   → FORWARD/BACKWARD/LEFT/RIGHT/DONE"));
  Serial.println(F("BRAKE               → Stop drill"));
  Serial.println(F("RPM                 → Show drill speed"));
  Serial.println(F("POS                 → Show encoder position"));
  Serial.println(F("LOAD                → Read load cell"));
  Serial.println(F("READCURRENT         → Read current sensor"));
  Serial.println(F("HELP                → This menu"));
  Serial.println(F("==========================\n"));
}

void loop() {
  // --- Serial command parser ---
  if (stringComplete) {
    processCommand(inputString);
    inputString = "";
    stringComplete = false;
  }

  // Optional: add background tasks here (e.g. auto-unscrew, monitoring)
}

void serialEvent() {
  while (Serial.available()) {
    char inChar = (char)Serial.read();
    if (inChar == '\n' || inChar == '\r') {
      if (inputString.length() > 0) {
        stringComplete = true;
      }
    } else if (inputString.length() < 60) {
      inputString += inChar;
    }
  }
}


/**
 * @brief Manual-assisted unscrew routine at given X,Y
 * @param x Target X coordinate
 * @param y Target Y coordinate
 * @return true if screw removed, false on failure/timeout
 */
bool runScrewRemovalFlow(float x, float y) {
  const float Z_STEP_ENGAGE = 0.5;     // mm per step
  const float Z_STEP_UNSCREW = 0.5;
  const float Z_MAX_TRAVEL   = 8.5;    // max Z travel from safe height
  const float UNSCREW_DRILL_DEGREES = -180;
  const int   DRILL_SPEED  = 255;
  const unsigned long DRILL_TIMEOUT = 8000;

  targetZ = SAFE_Z;

  // 1. Coordinates come from Serial today. Later, CV can call this same routine.
  Serial.println(F("Moving to screw coordinate at safe Z..."));
  Stepper_MoveTo(x, y, SAFE_Z);
  targetX = x;
  targetY = y;
  delay(500);

  Serial.println(F("Manual alignment at safe Z."));
  while (true) {
    int alignmentAction = LoadcellPi_GetAlignmentAction();

    if (alignmentAction == ALIGNMENT_ACTION_DONE) {
      break;
    }

    if (alignmentAction == ALIGNMENT_ACTION_FORWARD) {
      y += SCREW_ALIGNMENT_NUDGE_MM;
    } else if (alignmentAction == ALIGNMENT_ACTION_BACKWARD) {
      y -= SCREW_ALIGNMENT_NUDGE_MM;
    } else if (alignmentAction == ALIGNMENT_ACTION_LEFT) {
      x -= SCREW_ALIGNMENT_NUDGE_MM;
    } else if (alignmentAction == ALIGNMENT_ACTION_RIGHT) {
      x += SCREW_ALIGNMENT_NUDGE_MM;
    }

    Stepper_MoveTo(x, y, SAFE_Z);
    targetX = x;
    targetY = y;
    Serial.print(F("Adjusted X="));
    Serial.print(x, 2);
    Serial.print(F(" Y="));
    Serial.println(y, 2);
  }

  // 2. Lower slowly until contact. The prompt is the feedback loop placeholder.
  Serial.println(F("Lowering slowly until screw contact..."));
  while (targetZ < SAFE_Z + Z_MAX_TRAVEL) {
    int action = LoadcellPi_GetApproachAction();

    if (action == LOADCELL_ACTION_STOP) {
      break;
    }

    if (action == LOADCELL_ACTION_DOWN) {
      targetZ += Z_STEP_ENGAGE;
    } else if (action == LOADCELL_ACTION_UP) {
      targetZ -= Z_STEP_ENGAGE;
    }

    Stepper_MoveTo(x, y, targetZ);
    Serial.print(F("Z="));
    Serial.println(targetZ, 1);
  }

  if (targetZ >= SAFE_Z + Z_MAX_TRAVEL) {
    Serial.println(F("Contact search exceeded Z travel limit."));
    return false;
  }

  Serial.println(F("Screw touching"));

  // 3. Unscrew in small manual-confirmed passes. Later sensor checks can replace prompts.
  while (true) {
    Serial.println(F("Unscrewing a little..."));
    bool drillOk = Motor_RotateDegrees(UNSCREW_DRILL_DEGREES, DRILL_SPEED, DRILL_TIMEOUT);
    if (!drillOk) {
      Serial.println(F("Drill timeout."));
      return false;
    }

    if (LoadcellPi_DidScrewDrop()) {
      Serial.println(F("Screw drop confirmed."));
      break;
    }

    if (!LoadcellPi_ShouldTryAnotherUnscrewPass()) {
      Serial.println(F("Operator stopped unscrew sequence."));
      return false;
    }

    Serial.println(F("Lowering/picking before next pass..."));
    while (targetZ < SAFE_Z + Z_MAX_TRAVEL) {
      if (!LoadcellPi_ShouldLowerForUnscrew()) {
        break;
      }
      targetZ += Z_STEP_UNSCREW;
      Stepper_MoveTo(x, y, targetZ);
      Serial.print(F("Z="));
      Serial.println(targetZ, 1);
    }
  }

  // 4. Retract and move to magnet/drop-off location.
  targetZ = SAFE_Z;
  Stepper_MoveTo(x, y, SAFE_Z);
  Motor_Brake();
  Serial.println(F("Moving to screw drop-off location..."));
  Stepper_MoveTo(SCREW_DROPOFF_X, SCREW_DROPOFF_APPROACH_Y, SAFE_Z);
  Stepper_MoveTo(SCREW_DROPOFF_X, SCREW_DROPOFF_Y, SAFE_Z);
  targetX = SCREW_DROPOFF_X;
  targetY = SCREW_DROPOFF_Y;

  return true;
}

void processCommand(String cmd) {
  cmd.trim();
  cmd.toUpperCase();

  Serial.print(F("> "));
  Serial.println(cmd);

  /* --------------------------------------------------- */
  /*  HELP                                               */
  /* --------------------------------------------------- */
  if (cmd == "HELP") {
    printHelp();
    return;
  }

  /* --------------------------------------------------- */
  /*  HOME                                               */
  /* --------------------------------------------------- */
  if (cmd == "HOME") {
    Serial.println(F("Homing all steppers..."));
    Stepper_HomeAll();
    Serial.println(F("Homed."));
    return;
  }

  /* --------------------------------------------------- */
  /*  GOTO X Y Z                                         */
  /* --------------------------------------------------- */
  if (cmd.startsWith("GOTO ")) {
    String args = cmd.substring(5);
    args.trim();

    float x, y, z;
    int firstSpace = args.indexOf(' ');
    int secondSpace = args.indexOf(' ', firstSpace + 1);

    if (firstSpace > 0 && secondSpace > 0) {
      x = args.substring(0, firstSpace).toFloat();
      y = args.substring(firstSpace + 1, secondSpace).toFloat();
      z = args.substring(secondSpace + 1).toFloat();

      Serial.print(F("Moving to X=")); Serial.print(x, 2);
      Serial.print(F(" Y=")); Serial.print(y, 2);
      Serial.print(F(" Z=")); Serial.println(z, 2);

      Stepper_MoveTo(x, y, z);
      targetX = x;
      targetY = y;
      targetZ = z;
      Serial.println(F("Move complete."));
    } else {
      Serial.println(F("Error: GOTO X Y Z  (use spaces, no commas)"));
    }
    return;
  }

  /* --------------------------------------------------- */
  /*  DRILL degrees [speed]                              */
  /* --------------------------------------------------- */
  if (cmd.startsWith("DRILL ")) {
    String args = cmd.substring(6); // everything after "DRILL "
    args.trim();

    float deg = 0.0;
    int speed = 180; // default PWM speed

    int spaceIndex = args.indexOf(' ');
    if (spaceIndex >= 0) {
        // There is a second value for speed
        String degStr = args.substring(0, spaceIndex);
        String speedStr = args.substring(spaceIndex + 1);
        deg = degStr.toFloat();
        speed = speedStr.toInt();
    } else {
        // Only degrees given
        deg = args.toFloat();
    }

    // Clamp speed
    if (speed < 0)   speed = 0;
    if (speed > 255) speed = 255;

    Serial.print(F("Rotating "));
    Serial.print(deg, 2);
    Serial.print(F(" degrees at PWM "));
    Serial.println(speed);

    bool ok = Motor_RotateDegrees(deg, speed, 10000);
    Serial.println(ok ? F("Done.") : F("TIMEOUT!"));
    return;
}

  /* --------------------------------------------------- */
  /*  BRAKE / RPM / POS / LOAD / READCURRENT             */
  /* --------------------------------------------------- */
  if (cmd == "BRAKE") {
    Motor_Brake();
    Serial.println(F("Drill stopped."));
    return;
  }
  if (cmd == "RPM") {
    float rpm = Encoder_GetSpeedRPM();
    Serial.print(F("Drill RPM: "));
    Serial.println(rpm, 1);
    return;
  }
  if (cmd == "POS") {
    long pos = Encoder_GetPosition();
    float deg = pos * 360.0f / 1440.0f;
    Serial.print(F("Encoder: "));
    Serial.print(pos);
    Serial.print(F(" pulses ("));
    Serial.print(deg, 2);
    Serial.println(F(" degrees)"));
    return;
  }
  if (cmd == "LOAD") {
    float load = Loadcell_Read();
    Serial.print(F("Load cell: "));
    Serial.println(load, 3);
    return;
  }
  if (cmd == "READCURRENT") {
    double current_sensor = read_current_sensor();
    Serial.print(F("current sensor: "));
    Serial.println(current_sensor, 3);
    return;
  }

  /* --------------------------------------------------- */
  /*  UNSCREW X Y  - Manual-assisted unscrew routine     */
  /* --------------------------------------------------- */
  if (cmd.startsWith("UNSCREW ")) {
    String args = cmd.substring(8);
    args.trim();

    float x = 0.0;
    float y = 0.0;

    int spaceIndex = args.indexOf(' ');
    if (spaceIndex >= 0) {
        // Split into X and Y parts
        String xStr = args.substring(0, spaceIndex);
        String yStr = args.substring(spaceIndex + 1);
        xStr.trim();
        yStr.trim();
        x = xStr.toFloat();
        y = yStr.toFloat();

        Serial.print(F("Starting UNSCREW at X="));
        Serial.print(x, 2);
        Serial.print(F(" Y="));
        Serial.println(y, 2);

        bool success = runScrewRemovalFlow(x, y);
        Serial.println(success ? F("UNSCREW complete.") : F("UNSCREW failed."));
    } else {
        Serial.println(F("Error: UNSCREW X Y"));
    }
    return;
  }

  /* --------------------------------------------------- */
  /*  UNSCREWCHAIN [n] x1 y1 x2 y2 ... xn yn             */
  /*  Example: UNSCREWCHAIN 3 100 200 150 250 200 300    */
  /* --------------------------------------------------- */
  if (cmd.startsWith("UNSCREWCHAIN ")) {
    String args = cmd.substring(13);
    args.trim();

    if (args.length() == 0) {
      Serial.println(F("Error: UNSCREWCHAIN [count] x1 y1 x2 y2 ..."));
      return;
    }

    // Parse number of points (optional — if not given, count pairs)
    int numPoints = 0;
    int firstSpace = args.indexOf(' ');

    if (firstSpace == -1) {
      Serial.println(F("Error: No coordinates provided."));
      return;
    }

    String firstToken = args.substring(0, firstSpace);
    args = args.substring(firstSpace + 1);
    args.trim();

    // Try to read count as integer
    numPoints = firstToken.toInt();

    // Now parse X/Y pairs from remaining args
    float points[50][2];  // max 50 screws
    int idx = 0;

    String remaining = args + " ";
    while (remaining.length() > 1 && idx < numPoints) {
      int spacePos = remaining.indexOf(' ');
      if (spacePos == -1) break;

      String xStr = remaining.substring(0, spacePos);
      remaining = remaining.substring(spacePos + 1);
      spacePos = remaining.indexOf(' ');
      if (spacePos == -1) {
        Serial.println(F("Error: Missing Y coordinate."));
        return;
      }

      String yStr = remaining.substring(0, spacePos);
      remaining = remaining.substring(spacePos + 1);

      xStr.trim(); yStr.trim();
      float x = xStr.toFloat();
      float y = yStr.toFloat();

      if (abs(x) > 240 || abs(y) > 300) {  // sanity check
        Serial.println(F("Warning: Coordinate out of range, skipping."));
        continue;
      }

      points[idx][0] = x;
      points[idx][1] = y;
      idx++;
    }

    if (idx != numPoints) {
      Serial.print(F("Warning: Only found "));
      Serial.print(idx);
      Serial.print(F(" of "));
      Serial.print(numPoints);
      Serial.println(F(" points."));
    }

    // --- Execute chain ---
    Serial.println(F("Starting UNSCREWCHAIN sequence..."));
    int successCount = 0;

    for (int i = 0; i < idx; i++) {
      float x = points[i][0];
      float y = points[i][1];

      Serial.print(F("--- Screw "));
      Serial.print(i + 1);
      Serial.print(F("/"));
      Serial.print(idx);
      Serial.print(F(" at X="));
      Serial.print(x, 2);
      Serial.print(F(" Y="));
      Serial.println(y, 2);

      bool success = runScrewRemovalFlow(x, y);

      if (success) {
        successCount++;
        Serial.println(F("Screw removed."));
      } else {
        Serial.println(F("Failed to remove screw."));
        // Optional: continue anyway or abort?
      }

      // Small pause between screws (avoid thermal issues, give time to drop screw)
      delay(1000);
    }

    Serial.println(F("UNSCREWCHAIN complete."));
    Serial.print(successCount);
    Serial.print(F("/"));
    Serial.print(idx);
    Serial.println(F(" screws removed."));

    return;
  }

  /* --------------------------------------------------- */
  /*  Unknown                                            */
  /* --------------------------------------------------- */
  Serial.println(F("Unknown command. Type HELP."));
}
