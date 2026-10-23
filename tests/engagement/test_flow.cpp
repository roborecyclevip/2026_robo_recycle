#include "Arduino.h"
#include "ScrewEngagement.h"
#include <cassert>
#include <vector>
#include <iostream>

uint64_t fakeUs = 0;
int pins[64] = {};
unsigned long stopAt = 0;
bool stopSent = false;
FakeSerial Serial;
struct Position { float x, y, z; } position;
std::vector<Position> moves;
unsigned long motorStart = 0, moveStart = 0;
int motorRuns = 0;
bool spinning = false, moving = false, stuck = false;
bool rpmDrop = false, currentRise = false, invalidBaseline = false;
float destination = 0;
int descentSamples = 0;

void Motor_Brake() { spinning = false; }
void Motor_Forward(int) { spinning = true; motorStart = fakeUs / 1000; ++motorRuns; }
void Motor_Backward(int speed) { Motor_Forward(speed); }
void Encoder_Reset() {}
float Encoder_GetSpeedRPM() {
  auto elapsed = fakeUs / 1000 - motorStart;
  if (elapsed < 500 || invalidBaseline) return 0;
  return motorRuns == 2 && (moving || position.z >= 100) && rpmDrop ? -390 : -414;
}
double read_current_sensor() {
  if (moving) ++descentSamples;
  // Large startup current must never be classified as engagement.
  if (fakeUs / 1000 - motorStart < 500) return 4;
  return motorRuns == 2 && (moving || position.z >= 100) && currentRise ? .95 : .72;
}
void Stepper_MoveTo(float x, float y, float z) {
  assert(!spinning); // All blocking moves happen with the drill braked.
  position = {x,y,z}; moves.push_back(position);
}
void Stepper_GetPosition(float &x, float &y, float &z) { x=position.x; y=position.y; z=position.z; }
bool Stepper_StartZMove(float z) {
  assert(spinning);
  destination = z; moving = true; moveStart = fakeUs / 1000;
  return true;
}
void Stepper_ServiceZMove() {
  if (!moving || stuck) return;
  float fraction = (fakeUs / 1000 - moveStart) / 1600.f;
  if (fraction >= 1) { fraction = 1; moving = false; }
  position.z = 80 + 20 * fraction;
  assert(position.z <= 100);
}
bool Stepper_ZMoveBusy() { return moving; }
void Stepper_StopZMove() { moving = false; }

void reset() {
  fakeUs=0; stopAt=0; stopSent=false; Serial.output.str(""); Serial.stopIndex=0;
  moves.clear(); position={10,20,110}; motorRuns=0; spinning=moving=stuck=false;
  rpmDrop=currentRise=invalidBaseline=false; descentSamples=0;
}
int main() {
  for (int mode = 0; mode < 4; ++mode) {
    reset(); rpmDrop=mode & 1; currentRise=mode & 2;
    auto result=unscrew_screw_engagement(30,40,100,180,300);
    assert(result == (mode == 3 ? ScrewEngagementResult::Engaged : ScrewEngagementResult::NotEngaged));
    assert(!spinning && !moving && motorRuns==2 && descentSamples>40);
    assert(moves.size()==4 && moves[0].x==10 && moves[0].y==20 && moves[0].z==80);
    assert(position.x==30 && position.y==40 && position.z==80);
  }
  reset(); invalidBaseline=true;
  assert(unscrew_screw_engagement(30,40,100)==ScrewEngagementResult::Aborted);
  assert(motorRuns==1 && !spinning && !moving);
  reset(); stopAt=3800; // stop during descent, after both startup periods
  assert(unscrew_screw_engagement(30,40,100)==ScrewEngagementResult::Aborted);
  assert(!spinning && !moving && position.z>80 && position.z<100 && moves.size()==3);
  reset(); stuck=true;
  assert(unscrew_screw_engagement(30,40,100)==ScrewEngagementResult::Aborted);
  assert(!spinning && !moving);
  reset();
  assert(unscrew_screw_engagement(30,40,10)==ScrewEngagementResult::Aborted);
  assert(moves.empty() && motorRuns==0);
  std::cout << "Flow tests passed\n";
}
