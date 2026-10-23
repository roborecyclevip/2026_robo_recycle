#include "EngagementDetection.h"
#include <cassert>
#include <iostream>

int main() {
  EngagementCurrentAverage average;
  assert(average.add(1) == 1);
  assert(average.add(3) == 2);
  average.add(5); average.add(7); average.add(9);
  assert(average.add(11) == 7);

  EngagementBaseline baseline;
  for (int i = 0; i < 50; ++i) baseline.add(-414, .72f);
  assert(baseline.valid());
  EngagementBaseline stopped;
  for (int i = 0; i < 50; ++i) stopped.add(0, .72f);
  assert(!stopped.valid());

  EngagementDetector normal(414, .72f), currentOnly(414, .72f), rpmOnly(414, .72f);
  for (int t = 0; t < 1000; t += 20) {
    assert(!normal.update(t, -414, .72f));
    assert(!currentOnly.update(t, -414, 1.0f));
    assert(!rpmOnly.update(t, -390, .72f));
  }
  EngagementDetector repeated(414, .72f);
  assert(!repeated.update(0, -390, .9f));
  assert(!repeated.update(20, -390, .9f)); // cached RPM is not new evidence
  assert(repeated.update(100, -390, .9f));
  assert(repeated.update(1000, -414, .72f)); // result stays latched

  EngagementDetector unrelated(414, .72f);
  assert(!unrelated.update(0, -414, 1));
  assert(!unrelated.update(500, -390, .72f));
  assert(!unrelated.update(600, -390, .72f));

  // Actual averaged-current/RPM samples from the supplied contact trace.
  const float rpm[] = {416,416,416,416,416,384.67,384.67,384.67,384.67,384.67,401.33};
  const float current[] = {.573,.663,.758,.774,.822,.917,.832,.769,.806,.874,.774};
  // Means from the complete log's 1000..1980 ms baseline, rather than rounded estimates.
  EngagementDetector recorded(413.2544f, .71584f);
  bool found = false;
  for (unsigned int i = 0; i < 11; ++i) found = recorded.update(3320 + i * 20, -rpm[i], current[i]);
  assert(found);

  // Time subtraction remains correct across a 32-bit clock rollover.
  EngagementDetector rollover(414, .72f);
  assert(!rollover.update(UINT32_MAX - 50, -390, .9f));
  assert(rollover.update(60, -390, .9f));
  std::cout << "Detection tests passed\n";
}
