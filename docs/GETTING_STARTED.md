# Getting Started

This guide is for students who are new to Arduino, Raspberry Pi, and this project.

## First, Understand The Split

In this project, the two computers do different jobs:

| Device | Job in this project |
| --- | --- |
| Arduino Mega 2560 | Controls motors, reads sensors, handles timing-critical actions |
| Raspberry Pi or laptop | Sends text commands over USB serial, such as `HOME` or `UNSCREW 233.5 195.0` |

If you only remember one thing, remember this:

- the Arduino runs the robot
- the Raspberry Pi just talks to the Arduino

## Safety Before Testing

Do these before moving anything:

1. Keep hands, loose clothing, and cables away from the gantry and drill.
2. Make sure the machine can be powered off quickly.
3. Test with no workpiece first.
4. Confirm the tool head has enough clearance before any move.
5. Never start with `UNSCREW`. Start with `HELP`, `HOME`, `LOAD`, and small `GOTO` moves.

## What You Need

### Hardware

- Arduino Mega 2560
- Repurposed Ultimaker gantry or equivalent 3-axis frame
- X, Y, and Z stepper motors
- Stepper drivers and CNC-style wiring
- DC drill motor with encoder
- DC motor driver
- Load cell and HX711 amplifier
- X, Y, and Z end stops
- USB cable from host computer to Arduino

### Software

- Arduino IDE
- Python 3 on the Raspberry Pi or laptop if you want to use the Python scripts
- A serial terminal such as Arduino Serial Monitor, `screen`, or `minicom`

### Libraries Used By The Main Firmware

The main firmware references these Arduino libraries:

- `HX711`
- `MultiStepperLite`

Important:

- these libraries are not bundled in this repository
- you will need to install or copy them before `main.ino` will compile

Older test sketches also use:

- `AccelStepper`
- `Encoder` by Paul Stoffregen

Python scripts use:

- `pyserial`

## The Most Important Folder

The current system lives here:

`System Integration/main/`

If you are overwhelmed by the repo, start there and ignore `Test files/` until later.

## Your First Bring-Up Checklist

### 1. Open the main Arduino sketch

Open:

`System Integration/main/main.ino`

This is the firmware that matches the current README and handover notes.

### 2. Select the board

In Arduino IDE:

- choose Arduino Mega 2560
- choose the correct COM or USB port

### 3. Install missing libraries

If compilation fails because a header is missing, it is probably one of these:

- `HX711.h`
- `MultiStepperLite.h`

Add those libraries first, then compile again.

### 4. Upload the sketch

Once uploaded, open Serial Monitor at:

`115200` baud

The current main firmware prints startup messages and a help prompt.

### 5. Try these commands in order

```text
HELP
HOME
LOAD
GOTO 210.5 169.5 140
DRILL -90 180
BRAKE
```

What each command is checking:

- `HELP`: proves the serial connection works
- `HOME`: checks end stops and axis directions
- `LOAD`: checks the load cell path is alive
- `GOTO`: checks coordinate motion
- `DRILL`: checks the drill motor, encoder, and driver

## Logging Drill Current

Use `LOGDRILL duration_ms speed [sample_ms]` to print CSV telemetry to the serial
monitor. For example, `LOGDRILL 3000 100 50` runs for 3 seconds at speed 100 and
prints a row every 50 ms. The default interval is 50 ms and the minimum is 20 ms.
This command does not automatically save a CSV file.

The columns are `time_ms,rpm,current_A,encoder_count,current_avg_A`.
Both current columns are in amps. Plot `current_avg_A` for the smoother trend
and compare `current_A` to see brief spikes. CSV readers must accept the new
fifth column.

The moving average uses the latest 5 logged readings and resets for each run.
During startup, it averages only the samples collected so far. At 50 ms
intervals, a full window spans 200 ms and introduces about 100 ms of lag for
gradual changes. Short spikes are reduced in the average. Increasing the sample
interval increases the smoothing time and lag. To change the window size,
adjust `DRILL_CURRENT_AVERAGE_SAMPLES` in `main.ino` and upload again.

## Main Serial Commands

### Sensor-based screw engagement test

Upload the updated firmware, home the gantry, and use:

```text
UNSCREW_ENGAGE X Y Z [signed_speed] [finish_ms]
```

Replace X/Y/Z with measured screw coordinates. **Z is the expected engagement
height and the deepest permitted descent**, not a clearance height. On this
machine positive Z moves downward, so the approach height is `Z - 20 mm`.
Z must be at least 20 mm; X/Y must be nonnegative. Coordinates must be within
your machine's actual travel, as the existing motion system has no software
travel envelope. The default speed is PWM `180` and the default finishing spin
is `3000` ms. Negative PWM reverses the drill. Match the direction to your bit
and screw. Optional PWM must be an integer from -255 to 255 excluding zero;
finishing time must be an integer from 1 to 30000 ms.

The routine:

1. Brakes the drill and raises Z if needed before travelling across X/Y, then
   positions the tool 20 mm above the expected engagement height.
2. Spins at clearance, ignores the first second of startup, and measures RPM
   magnitude and 5-sample averaged current over the next second. It prints their
   means and ranges. A stopped or substantially changing RPM baseline cancels
   the test before descent.
3. Brakes for 500 ms, restarts, and waits another second at clearance so the
   second startup surge is excluded from detection.
4. Moves **directly** to the supplied engagement Z at the same step interval as
   `GOTO`, with the drill spinning. It services Z movement and samples telemetry
   together, then holds that Z while spinning for the finishing time. It does
   this whether or not engagement is detected; detection does not request
   further downward travel.
5. Brakes, retracts 20 mm vertically, and prints either
   `Screw engagement detected (RPM drop + current rise).` or
   `Screw engagement NOT detected.`

The initial detector requires an RPM magnitude drop of at least **2.5%** from the
baseline on two checks 100 ms apart, plus an averaged-current rise of at least
**0.08 A** within the preceding 200 ms. A match stays recorded for the rest of
the test. Tune these experimental values in `EngagementDetection.h` using
free-spinning and contact runs. Sensor-indicated contact does not prove the bit
is seated in the screw or that the screw was removed.

CSV telemetry is printed every 20 ms, with columns:

```text
time_ms,phase,z_mm,rpm,current_A,current_avg_A,engaged
```

Time restarts at each phase; descent and finishing share a clock. `engaged` is
0 until a match, then 1. Startup rows are visible for inspection but excluded
from detection. Output is sent over serial; no CSV file is saved automatically.

Send `BRAKE` followed by a newline to abort during baseline sampling, the restart
wait, descent, or finishing. An abort brakes the drill and stops Z, reports an
aborted result, and stays at that position. Initial positioning and final
retraction use the existing blocking movement calls, which cannot process
serial commands during those moves. A descent lasting over 10 seconds also
aborts. Other commands received during sampling are discarded.

The encoder now counts only actual A-channel edges, including when an older
routine polls it. Previously polling could add artificial counts, so the new
free-spin RPM may differ from earlier `LOGDRILL` readings. Baselines are measured
again for every test. Signed RPM is logged; detection compares its magnitude.

Implementation is in `ScrewEngagement.cpp`; cooperative Z servicing is in
`STEPPERmotor.cpp`. Native simulations can be run with
`python3 tests/engagement/run_tests.py` (requires g++ and the installed
MultiStepperLite source). They cover the supplied contact-trace excerpt,
isolated signals, startup exclusion, detection and non-detection paths,
aborts/timeouts, encoder polling, and Z position tracking. Hardware testing is
still needed to tune the detector and verify clearance/coordinates.

The main firmware accepts these commands over serial at `115200` baud:

| Command | Example | What it does |
| --- | --- | --- |
| `HELP` | `HELP` | Prints the command menu |
| `HOME` | `HOME` | Homes Z, then X, then Y |
| `GOTO X Y Z` | `GOTO 210.5 169.5 140` | Moves to an absolute position in millimetres |
| `DRILL degrees [speed]` | `DRILL -90 180` | Rotates the drill motor by a requested angle |
| `BRAKE` | `BRAKE` | Stops the drill motor |
| `RPM` | `RPM` | Prints drill speed estimate |
| `POS` | `POS` | Prints encoder position in pulses and degrees |
| `LOAD` | `LOAD` | Prints the current load-cell reading |
| `UNSCREW X Y` | `UNSCREW 233.5 195.0` | Runs the automated unscrewing routine at one XY point |
| `UNSCREWCHAIN ...` | `UNSCREWCHAIN 3 100 200 110 210 120 220` | Intended to run multiple points, but currently still uses built-in hard-coded points |

For beginners, the safest order is:

1. `HELP`
2. `HOME`
3. `LOAD`
4. `GOTO`
5. `DRILL`
6. `UNSCREW`

## Running From A Raspberry Pi

The current repo includes:

- `System Integration/Unscrew.py`

It opens `/dev/ttyACM0` at `115200` baud and sends `UNSCREW` commands for a list of hard-coded positions.

Before using it:

1. Confirm the Arduino is visible on the Pi as `/dev/ttyACM0` or update the script.
2. Install `pyserial`.
3. Make sure manual serial commands already work.

Do not use the older scripts in `Test files/` as your starting point. They mostly use `9600` baud and were written for earlier experiments.

## Understanding Coordinates

The current system uses millimetres.

- origin is set by homing
- X moves toward the Ultimaker glass panel
- Y moves parallel to the glass panel
- increasing Z moves the tool down toward the workpiece

The current hard-coded test points are:

```text
(233.5, 195.0)  (233.5, 182.5)  (233.5, 169.5)
(222.0, 195.0)  (222.0, 182.5)  (222.0, 169.5)
(210.5, 195.0)  (210.5, 182.5)  (210.5, 169.5)
```

These are only for one known hard drive layout. Re-measure them for any new workpiece.

## Before You Run `UNSCREW`

Check all of these first:

- homing works on all three axes
- `GOTO` moves in the expected direction
- the drill rotates the expected direction for negative degrees
- the load cell gives stable readings
- the tool can reach the screw safely
- the workpiece is clamped securely

## Calibration Notes

The `UNSCREW` routine depends heavily on load-cell thresholds.

The current code in `System Integration/main/main.ino` uses the same placeholder-style value for all three thresholds:

- `ENGAGE_LOAD`
- `Z_UNSCREW_THRESHOLD`
- `DRILL_STOP_THRESHOLD`

In the current repo state, all three are set to `-1300000.000` inside `autoUnscrew()`.

Treat that as a starting point only, not a guaranteed correct value.

Archived handover material reported example raw readings around:

- baseline: about `2154000`
- light contact: about `2012000`
- screw releasing: about `1630000`

Those numbers came from earlier testing and may not match your hardware. Use your own measured readings on the real machine.

## Common Beginner Mistakes

- Using the old test sketches and expecting them to match the main firmware
- Forgetting that the main firmware uses `115200` baud, not `9600`
- Running `UNSCREW` before checking `HOME`, `LOAD`, and `GOTO`
- Assuming the Raspberry Pi controls the motors directly
- Assuming the hard-coded screw coordinates work for every drive

## If Something Does Not Work

Start with the simplest possible test:

1. Can the Arduino connect over serial?
2. Can it print the `HELP` menu?
3. Can each axis home?
4. Can the drill rotate?
5. Can the load cell print numbers?

Only move on once the previous step works.
