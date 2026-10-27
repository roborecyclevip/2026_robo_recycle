# Robo-Recycle

Robo-Recycle is an automated screw-removal system for hard drive disassembly. The current build uses a repurposed Ultimaker gantry, an Arduino Mega 2560 for real-time motor control, and a Raspberry Pi or laptop as a serial-command host.

This documentation refresh was written for new students on 2026-04-14 using:

- the code in this repository
- the archived handover deck `RoboRecycle_Handover  -  Repaired.pptx`
- the archived report `Robo-Recycle 2025 Report.docx`

## Start Here

If you are new to this project, read these in order:

1. [Getting started](docs/GETTING_STARTED.md)
2. [Components and wiring](docs/COMPONENTS_AND_WIRING.md)
3. [Codebase guide](docs/CODEBASE_GUIDE.md)

Reference material:

- [Legacy README snapshot](docs/README_LEGACY_2026-04-14.md)

## What This Project Currently Does

- Homes a 3-axis gantry with end stops
- Moves the tool head to absolute X/Y/Z positions
- Rotates a DC drill motor by a requested number of degrees using encoder feedback
- Logs spindle RPM and motor current, including a five-sample current average
- Runs a manual-assisted `UNSCREW` routine at a supplied XY position
- Provides a separate experimental `UNSCREW_ENGAGE` test using RPM drop and current rise

## System Flowchart

![Current workflow and planned RPM/current engagement](docs/images/system_flowchart.svg)

See [the updated flowchart and implementation notes](docs/SYSTEM_FLOWCHART.md). The physical load cell has been removed. The normal removal cycle still uses operator prompts; automatic RPM/current engagement hand-off is planned, not yet integrated.

## High-Level Architecture

```mermaid
flowchart LR
  Host["Raspberry Pi or laptop"] -->|"USB serial"| Mega["Arduino Mega 2560"]
  Mega --> Stepper["CNC shield / stepper drivers"]
  Stepper --> XYZ["X, Y, Z stepper motors"]
  Mega --> Driver["DC motor driver"]
  Driver --> Drill["Drill motor with encoder"]
  Encoder["Spindle encoder / RPM"] --> Mega
  Current["Motor current sensor"] --> Mega
  Camera["Overhead camera"] -. "Future automated screw coordinates" .-> Host
  Mega --> Endstops["X, Y, Z end stops"]
```

## Quick Start

1. Open [docs/GETTING_STARTED.md](docs/GETTING_STARTED.md).
2. Install the required Arduino libraries. The main firmware depends on `HX711` and `MultiStepperLite`, which are referenced by the code but not bundled in this repo.
3. Open `System Integration/main/main.ino` in Arduino IDE and upload it to the Arduino Mega 2560.
4. Open a serial monitor at `115200` baud and run `HELP`, `HOME`, `RPM`, `READCURRENT`, and `GOTO`.
5. Check end stops, motor direction, tool clearance and operator prompts before running `UNSCREW` on your hardware.

## Current Status

This is a partially working lab prototype, not a polished turnkey system.

Known limitations:

- `UNSCREWCHAIN` uses a coordinate list, but contact and release decisions remain manual; it currently continues after a failed screw.
- Legacy load-cell initialisation and prompt wording remain in firmware even though the physical sensor is removed.
- Experimental RPM/current thresholds need tuning and do not prove that the bit is seated; the test does not yet trigger automatic reversal or the main removal routine.
- The screw-retention approach is magnetic, so it may not hold non-magnetic screws.
- Several files in `Test files/` are older experiments and use different baud rates and command formats from the main system.

## Main Entry Points

- `System Integration/main/main.ino`: main Arduino firmware
- `System Integration/Unscrew.py`: simple Python script that sends repeated `UNSCREW` commands
- `Test files/`: older experiments for end stops, force testing, homing, and serial control

## Recommended Reading Order In The Code

1. `System Integration/main/main.ino`
2. `System Integration/main/STEPPERmotor.cpp`
3. `System Integration/main/DCmotor.cpp`
4. `System Integration/main/Encoder.cpp`
5. `System Integration/main/Loadcell.cpp`
