# Codebase Guide

This guide explains what each part of the repository is for and which files you should care about first.

## Top-Level Layout

| Path | What it is | Should a new student use it first |
| --- | --- | --- |
| `README.md` | Project overview and doc links | Yes |
| `System Integration/` | Current integrated system | Yes |
| `Test files/` | Older experiments and subsystem tests | Later |

## Recommended Reading Order

If you want the shortest path to understanding the project, read these in order:

1. `README.md`
2. `docs/GETTING_STARTED.md`
3. `System Integration/main/main.ino`
4. `System Integration/main/STEPPERmotor.cpp`
5. `System Integration/main/DCmotor.cpp`
6. `System Integration/main/Encoder.cpp`
7. `System Integration/main/Loadcell.cpp`

## Current System Files

### `System Integration/main/main.ino`

This is the main Arduino program.

It does four big jobs:

- starts all subsystems in `setup()`
- reads serial commands such as `HOME`, `GOTO`, and `UNSCREW`
- runs the `autoUnscrew()` routine
- stores the hard-coded screw coordinate list in `hardCodePoints[]`

If you only open one code file, open this one first.

### `System Integration/main/STEPPERmotor.h` and `STEPPERmotor.cpp`

This module controls the X, Y, and Z axes.

It contains:

- pin definitions for step, direction, and end-stop inputs
- homing logic for each axis
- conversion from millimetres to step counts
- coordinated `Stepper_MoveTo(x, y, z)` motion

This file is the best place to look when:

- an axis moves the wrong direction
- homing fails
- coordinates seem wrong

### `System Integration/main/DCmotor.h` and `DCmotor.cpp`

This module controls the drill motor.

It contains:

- the motor-driver pin mapping
- forward and backward motor functions
- `Motor_RotateDegrees()`, which uses encoder feedback to stop after a requested angle

This is the best place to look when the drill spins the wrong way or never stops correctly.

### `System Integration/main/Encoder.h` and `Encoder.cpp`

This module counts encoder pulses and estimates RPM.

It contains:

- encoder pin mapping
- interrupt-based pulse counting
- speed calculation
- position reset logic

This matters because the drill control depends on encoder counts to rotate a known number of degrees.

### `System Integration/main/Loadcell.h` and `Loadcell.cpp`

This module wraps the HX711 load-cell amplifier.

It contains:

- load-cell pin mapping
- tare setup
- averaged load readings

This matters because `autoUnscrew()` uses the load-cell values to decide when the screw is touched and when it may have been released.

### `System Integration/Unscrew.py`

This is a simple host-side Python script.

It:

- opens `/dev/ttyACM0`
- connects at `115200` baud
- sends `UNSCREW x y` commands for a hard-coded list of screw positions

It is useful after manual serial testing works, but it is not where the robot logic lives.

## Test Files

The `Test files/` folder is useful, but it is mostly historical and experimental. Treat it as reference material, not the main system.

### Files that are still useful

| File | Purpose | Notes |
| --- | --- | --- |
| `Check_EndStop.ino` | Reads one end-stop input | Good for simple wiring checks |
| `ForceTesting.ino` | Basic HX711/load-cell test | Uses different pins from the main integration code |
| `Encoder/Encoder.ino` | Standalone encoder test | Uses the external `Encoder` library |
| `Simple_Move.ino` | Simple stepper movement test | Very early motion test |

### Files to treat as legacy prototypes

| File | Why it is legacy |
| --- | --- |
| `HomeWithPy.ino` | Older single-axis homing experiment |
| `HomeMoveWithPy.ino` | Older serial command format and `9600` baud |
| `gantry_control.py` | Written for older serial commands and `9600` baud |
| `serial_control.py` | Generic serial shell for older test firmware |
| `motorControl/` | Older DC motor control experiment with code that no longer matches the main module names |

## Archive Files Reviewed

The attached `OneDrive_2026-04-14.zip` contained a lot of project history. The most useful files for documentation were:

| Archive file | Why it mattered |
| --- | --- |
| `2025 Folder/Robo-Recycle 2025 Report.docx` | Confirmed hardware list, part names, Mega pin map, and subsystem ownership |
| `2025 Folder/RoboRecycle_Handover  -  Repaired.pptx` | Confirmed current operating concept, command list, known issues, and calibration examples |

Most of the rest of the archive appears to be weekly slide decks and general project records. Those may still be useful for history, but they were not needed to understand the current code layout.

## Known Mismatches To Keep In Mind

These are easy places for new students to get confused:

- main firmware uses `115200` baud, but several test files use `9600`
- `Unscrew.py` matches the current main firmware better than the older Python scripts do
- the archived handover slides mention older threshold placeholders, while the current repo code now uses `-1300000.000` for all three thresholds in `autoUnscrew()`
- `UNSCREWCHAIN` still uses the built-in 9-point array instead of the parsed input points

## If You Want To Make Your First Small Change

Good first tasks:

1. Add comments or print statements to `main.ino`
2. Test one subsystem at a time with the files in `Test files/`
3. Measure and document real load-cell thresholds for your exact machine
4. Fix `UNSCREWCHAIN` so it uses parsed coordinates instead of `hardCodePoints[]`
