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

void LoadcellPi_Init() {
}

bool LoadcellPi_IsContact() {
  return askYesNo("Has the load cell reached contact threshold?");
}

bool LoadcellPi_ShouldLowerForUnscrew() {
  return askYesNo("Should Z keep lowering for unscrew?");
}

bool LoadcellPi_ShouldKeepDrilling() {
  return askYesNo("Should the drill keep rotating?");
}

bool LoadcellPi_Tare() {
  return askYesNo("Tare load cell now?");
}
