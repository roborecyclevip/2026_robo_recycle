#include "Loadcell_pi.h"

static bool askYesNo(const char* prompt) {
  Serial.println(prompt);
  Serial.println("Type YES or NO:");

  String input = "";
  while (true) {
    while (Serial.available()) {
      char c = (char)Serial.read();

      if (c == '\n' || c == '\r') {
        input.trim();
        input.toUpperCase();

        if (input == "YES") {
          return true;
        }
        if (input == "NO") {
          return false;
        }

        input = "";
        Serial.println("Please type YES or NO:");
      } else {
        input += c;
      }
    }
  }
}

static int askApproachDirection() {
  Serial.println("Move UP or DOWN?");

  String input = "";
  while (true) {
    while (Serial.available()) {
      char c = (char)Serial.read();

      if (c == '\n' || c == '\r') {
        input.trim();
        input.toUpperCase();

        if (input == "UP") {
          return LOADCELL_ACTION_UP;
        }
        if (input == "DOWN") {
          return LOADCELL_ACTION_DOWN;
        }

        input = "";
        Serial.println("Please type UP or DOWN:");
      } else {
        input += c;
      }
    }
  }
}

static int askAlignmentDirection() {
  Serial.println("Nudge alignment? Type FORWARD, BACKWARD, LEFT, RIGHT, or DONE:");

  String input = "";
  while (true) {
    while (Serial.available()) {
      char c = (char)Serial.read();

      if (c == '\n' || c == '\r') {
        input.trim();
        input.toUpperCase();

        if (input == "DONE") {
          return ALIGNMENT_ACTION_DONE;
        }
        if (input == "FORWARD" || input == "F") {
          return ALIGNMENT_ACTION_FORWARD;
        }
        if (input == "BACKWARD" || input == "BACK" || input == "B") {
          return ALIGNMENT_ACTION_BACKWARD;
        }
        if (input == "LEFT" || input == "L") {
          return ALIGNMENT_ACTION_LEFT;
        }
        if (input == "RIGHT" || input == "R") {
          return ALIGNMENT_ACTION_RIGHT;
        }

        input = "";
        Serial.println("Please type FORWARD, BACKWARD, LEFT, RIGHT, or DONE:");
      } else {
        input += c;
      }
    }
  }
}

void LoadcellPi_Init() {
}

int LoadcellPi_GetApproachAction() {
  if (askYesNo("Has the load cell reached contact threshold?")) {
    return LOADCELL_ACTION_STOP;
  }

  return askApproachDirection();
}

int LoadcellPi_GetAlignmentAction() {
  return askAlignmentDirection();
}

bool LoadcellPi_ShouldLowerForUnscrew() {
  return askYesNo("Should Z keep lowering for unscrew?");
}

bool LoadcellPi_ShouldKeepDrilling() {
  return askYesNo("Should the drill keep rotating?");
}

bool LoadcellPi_DidScrewDrop() {
  return askYesNo("Did the screw drop?");
}

bool LoadcellPi_ShouldTryAnotherUnscrewPass() {
  return askYesNo("Lower/pick and try another unscrew pass?");
}

bool LoadcellPi_Tare() {
  return askYesNo("Tare load cell now?");
}
