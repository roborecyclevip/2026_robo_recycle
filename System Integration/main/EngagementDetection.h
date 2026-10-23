#ifndef ENGAGEMENT_DETECTION_H
#define ENGAGEMENT_DETECTION_H

#include <stdint.h>
#include <math.h>

// Small, hardware-independent helpers so recorded logs can test the detector.
class EngagementCurrentAverage {
 public:
  float add(float current) {
    sum -= samples[index];
    samples[index] = current;
    sum += current;
    index = (index + 1) % 5;
    if (count < 5) ++count;
    return sum / count;
  }
 private:
  float samples[5] = {};
  float sum = 0;
  uint8_t count = 0;
  uint8_t index = 0;
};

struct EngagementBaseline {
  float rpmSum = 0, currentSum = 0;
  float rpmMin = 1e9f, rpmMax = 0;
  float currentMin = 1e9f, currentMax = -1e9f;
  unsigned int count = 0;

  void add(float rpm, float current) {
    rpm = fabsf(rpm); // Encoder direction must not reverse the drop comparison.
    rpmSum += rpm;
    currentSum += current;
    if (rpm < rpmMin) rpmMin = rpm;
    if (rpm > rpmMax) rpmMax = rpm;
    if (current < currentMin) currentMin = current;
    if (current > currentMax) currentMax = current;
    ++count;
  }
  float rpm() const { return count ? rpmSum / count : 0; }
  float current() const { return count ? currentSum / count : 0; }
  bool valid() const {
    // Reject a stopped drill or a baseline still ramping/changing substantially.
    return count >= 40 && rpm() >= 20 && rpmMax - rpmMin <= rpm() * 0.10f;
  }
};

class EngagementDetector {
 public:
  EngagementDetector(float baselineRpm, float baselineCurrent)
      : normalRpm(fabsf(baselineRpm)), normalCurrent(baselineCurrent) {}

  // Initial tuning values: ~10 RPM at a 414 RPM baseline, and +0.08 A.
  // These are experimental contact indicators, not proof that the bit is seated.
  static constexpr float RPM_DROP_FRACTION = 0.025f;
  static constexpr float CURRENT_RISE_A = 0.08f;
  static constexpr uint32_t COINCIDENCE_MS = 200;

  bool update(uint32_t now, float rpm, float averagedCurrent) {
    if (engaged) return true;
    if (averagedCurrent >= normalCurrent + CURRENT_RISE_A) {
      sawCurrentRise = true;
      lastCurrentRise = now;
    }
    // RPM is refreshed every 100 ms by Encoder_GetSpeedRPM(). Repeated CSV rows
    // containing that same cached RPM must not count as separate confirmations.
    if (!haveRpmCheck || uint32_t(now - lastRpmCheck) >= 100) {
      haveRpmCheck = true;
      lastRpmCheck = now;
      if (fabsf(rpm) <= normalRpm * (1.0f - RPM_DROP_FRACTION)) {
        if (lowRpmChecks < 2) ++lowRpmChecks;
      } else {
        lowRpmChecks = 0;
      }
    }
    if (lowRpmChecks >= 2 && sawCurrentRise &&
        uint32_t(now - lastCurrentRise) <= COINCIDENCE_MS) engaged = true;
    return engaged;
  }
 private:
  float normalRpm, normalCurrent;
  uint32_t lastRpmCheck = 0, lastCurrentRise = 0;
  uint8_t lowRpmChecks = 0;
  bool haveRpmCheck = false, sawCurrentRise = false, engaged = false;
};

#endif
