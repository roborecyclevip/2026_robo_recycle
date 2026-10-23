#include "ScrewEngagement.h"
#include "EngagementDetection.h"
#include "STEPPERmotor.h"
#include "DCmotor.h"
#include "Encoder.h"
#include "Current.h"
#include <string.h>

namespace {
constexpr float CLEARANCE_MM = 20.0f;
constexpr unsigned long SAMPLE_MS = 20;
constexpr unsigned long SPINUP_MS = 1000;
constexpr unsigned long BASELINE_MS = 1000;
constexpr unsigned long DESCENT_TIMEOUT_MS = 10000;

// Local command reader: the usual serialEvent() cannot run inside this routine.
// Only BRAKE is accepted here; other input is discarded, never queued for later.
class StopRequest {
 public:
  bool requested() {
    while (Serial.available()) {
      char c = Serial.read();
      if (c == '\n' || c == '\r') {
        text[length] = '\0';
        bool stop = strcmp(text, "BRAKE") == 0;
        length = 0;
        if (stop) return true;
      } else if (c != ' ' && c != '\t') {
        if (c >= 'a' && c <= 'z') c -= 'a' - 'A';
        if (length < sizeof(text) - 1) text[length++] = c;
      }
    }
    return false;
  }
 private:
  char text[16] = {};
  uint8_t length = 0;
};

void startDrill(int speed) {
  Encoder_Reset();
  if (speed > 0) Motor_Forward(speed);
  else Motor_Backward(-speed);
}

// Every telemetry row has the same shape, including during startup/baseline.
void printSample(unsigned long elapsed, const char *phase, float rpm,
                 float current, float average, bool engaged) {
  float x, y, z;
  Stepper_GetPosition(x, y, z);
  Serial.print(elapsed); Serial.print(',');
  Serial.print(phase); Serial.print(',');
  Serial.print(z, 3); Serial.print(',');
  Serial.print(rpm, 2); Serial.print(',');
  Serial.print(current, 3); Serial.print(',');
  Serial.print(average, 3); Serial.print(',');
  Serial.println(engaged ? 1 : 0);
}

// Wait at clearance while servicing serial and sampling. Startup readings are
// logged but deliberately excluded from the baseline and engagement detector.
bool sampleAtClearance(unsigned long duration, const char *phase,
                       StopRequest &stop, EngagementCurrentAverage &average,
                       EngagementBaseline *baseline = nullptr) {
  unsigned long start = millis(), lastSample = start - SAMPLE_MS;
  while (millis() - start < duration) {
    if (stop.requested()) return false;
    unsigned long now = millis();
    if (now - lastSample >= SAMPLE_MS) {
      lastSample = now;
      float rpm = Encoder_GetSpeedRPM();
      float current = read_current_sensor();
      float smoothed = average.add(current);
      if (baseline) baseline->add(rpm, smoothed);
      printSample(now - start, phase, rpm, current, smoothed, false);
    }
  }
  return true;
}

ScrewEngagementResult abortEngagement() {
  Motor_Brake();
  Stepper_StopZMove();
  // Stay at the stopped position; an explicit stop must not trigger retraction.
  Serial.println(F("Engagement test ABORTED; engagement result unavailable."));
  return ScrewEngagementResult::Aborted;
}
} // namespace

ScrewEngagementResult unscrew_screw_engagement(float x, float y, float z,
                                             int speed, unsigned long finishMs) {
  if (!isfinite(x) || !isfinite(y) || !isfinite(z) || x < 0 || y < 0 ||
      z < CLEARANCE_MM || speed == 0 || speed < -255 || speed > 255 ||
      finishMs == 0 || finishMs > 30000) {
    Serial.println(F("Invalid engagement coordinates/speed/duration; no movement."));
    return ScrewEngagementResult::Aborted;
  }

  Motor_Brake();
  const float approachZ = z - CLEARANCE_MM;
  float oldX, oldY, oldZ;
  Stepper_GetPosition(oldX, oldY, oldZ);

  // 1. Raise before crossing XY. Never traverse sideways at the screw height.
  Serial.println(F("Moving to screw XY, 20 mm above expected engagement Z..."));
  if (oldZ > approachZ) Stepper_MoveTo(oldX, oldY, approachZ);
  Stepper_MoveTo(x, y, oldZ < approachZ ? oldZ : approachZ);
  Stepper_MoveTo(x, y, approachZ);

  StopRequest stop;
  EngagementCurrentAverage average;
  EngagementBaseline baseline;
  Serial.println(F("time_ms,phase,z_mm,rpm,current_A,current_avg_A,engaged"));

  // 2. First run: discard the startup second, then measure a free-spin baseline.
  if (stop.requested()) return abortEngagement();
  startDrill(speed);
  if (!sampleAtClearance(SPINUP_MS, "baseline_spinup", stop, average) ||
      !sampleAtClearance(BASELINE_MS, "baseline", stop, average, &baseline))
    return abortEngagement();
  Motor_Brake();
  if (!baseline.valid()) {
    Serial.println(F("Free-spin baseline stopped/unstable; descent cancelled."));
    return abortEngagement();
  }
  Serial.print(F("Baseline |RPM| mean/min/max: "));
  Serial.print(baseline.rpm(), 2); Serial.print('/');
  Serial.print(baseline.rpmMin, 2); Serial.print('/'); Serial.println(baseline.rpmMax, 2);
  Serial.print(F("Baseline averaged current A mean/min/max: "));
  Serial.print(baseline.current(), 3); Serial.print('/');
  Serial.print(baseline.currentMin, 3); Serial.print('/'); Serial.println(baseline.currentMax, 3);
  Serial.print(F("Detection: |RPM| <= "));
  Serial.print(baseline.rpm() * (1 - EngagementDetector::RPM_DROP_FRACTION), 2);
  Serial.print(F(" and current_avg_A >= "));
  Serial.println(baseline.current() + EngagementDetector::CURRENT_RISE_A, 3);

  // 3. Brake for half a second, restart, and ignore the startup surge again.
  const unsigned long pauseStart = millis();
  while (millis() - pauseStart < 500) if (stop.requested()) return abortEngagement();
  average = EngagementCurrentAverage();
  startDrill(speed);
  if (!sampleAtClearance(SPINUP_MS, "restart_spinup", stop, average))
    return abortEngagement();

  // 4. Move directly to expected engagement Z at the usual gantry rate.
  // The move returns immediately; servicing it here lets the drill and sensing
  // continue together. Never descend beyond the supplied engagement coordinate.
  EngagementDetector detector(baseline.rpm(), baseline.current());
  if (!Stepper_StartZMove(z)) return abortEngagement();
  unsigned long start = millis(), lastSample = start - SAMPLE_MS, finishStart = 0;
  bool finishing = false, engaged = false;
  while (true) {
    if (stop.requested()) return abortEngagement();
    Stepper_ServiceZMove();
    unsigned long now = millis();
    if (!finishing && !Stepper_ZMoveBusy()) {
      finishing = true;
      finishStart = now;
    }
    if (!finishing && now - start >= DESCENT_TIMEOUT_MS) {
      Serial.println(F("Z descent timed out."));
      return abortEngagement();
    }
    if (now - lastSample >= SAMPLE_MS) {
      lastSample = now;
      float rpm = Encoder_GetSpeedRPM();
      float current = read_current_sensor();
      float smoothed = average.add(current);
      engaged = detector.update(now, rpm, smoothed);
      printSample(now - start, finishing ? "finish" : "descend", rpm, current, smoothed, engaged);
    }
    // Detection is observational: finish the SAME bounded spin either way.
    if (finishing && now - finishStart >= finishMs) break;
  }

  // 5. Stop, retract vertically, then report what the sensors indicated.
  Motor_Brake();
  Stepper_MoveTo(x, y, approachZ);
  Serial.println(engaged ? F("Screw engagement detected (RPM drop + current rise).")
                         : F("Screw engagement NOT detected."));
  return engaged ? ScrewEngagementResult::Engaged : ScrewEngagementResult::NotEngaged;
}
