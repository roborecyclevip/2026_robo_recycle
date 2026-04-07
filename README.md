# Robo Recycle — Automated Screw Removal System

An Arduino-based gantry robot that automatically locates and removes screws from hard drive lids as part of a university e-waste disassembly project. The system uses a 3-axis CNC gantry (repurposed Ultimaker 3D printer frame), a DC drill motor with encoder, and a load cell to detect screw engagement and drive the unscrewing sequence.

> **Project status:** Partially working. The `autoUnscrew` routine succeeds on most screws under ideal alignment conditions. Several threshold constants require tuning per-installation — see [Calibration](#calibration).

---

## Hardware

| Component | Details |
|---|---|
| Gantry frame | Repurposed Ultimaker 3D printer (XY + Z axes) |
| Microcontroller | Arduino (with CNC shield + stepper drivers) |
| Host computer | Raspberry Pi (acts as serial terminal only) |
| Stepper motors | MOONS MS17HD series, driven at 12V / 0.6 Vref |
| Drill motor | DC motor with quadrature encoder |
| Tool head | Magnetic screwdriver bit (current limitation — see [Known Issues](#known-issues)) |
| Load cell | Mounted beneath workpiece bed |
| End stops | Used for homing on all three axes |

---

## Software dependencies

- Arduino IDE (or PlatformIO)
- Custom libraries (included in repo):
  - `DCmotor.h` — PWM motor control and encoder-based degree rotation
  - `STEPPERmotor.h` — 3-axis movement and homing routines
  - `Encoder.h` — quadrature encoder read + RPM calculation
  - `Loadcell.h` — raw load cell ADC reads
- Raspberry Pi side: any serial terminal (e.g. `screen`, `minicom`, or Arduino Serial Monitor at **115200 baud**)

---

## Coordinate system

- **Origin:** Set at homing position (all end stops triggered)
- **X axis:** Moves toward the glass panel of the Ultimaker enclosure
- **Y axis:** Moves parallel to the glass panel
- **Z axis:** Moves vertically; increasing Z moves the tool **down** toward the workpiece

The 9 hard-coded screw positions for the test hard drive lid are:

| | Y = 195.0 | Y = 182.5 | Y = 169.5 |
|---|---|---|---|
| **X = 233.5** | (233.5, 195.0) | (233.5, 182.5) | (233.5, 169.5) |
| **X = 222.0** | (222.0, 195.0) | (222.0, 182.5) | (222.0, 169.5) |
| **X = 210.5** | (210.5, 195.0) | (210.5, 182.5) | (210.5, 169.5) |

All coordinates are in millimetres.

---

## Serial commands

Connect at **115200 baud**. Commands are case-insensitive. Type `HELP` for a quick reference at any time.

| Command | Arguments | Description |
|---|---|---|
| `HOME` | — | Home all three axes using end stops |
| `GOTO` | `X Y Z` | Move gantry to absolute coordinates |
| `DRILL` | `degrees [speed]` | Rotate drill by given degrees. Speed is PWM 0–255, default 180. Negative degrees = CCW (unscrewing direction) |
| `UNSCREW` | `X Y` | Run full automated unscrew routine at given XY position |
| `UNSCREWCHAIN` | *(see note)* | Run unscrew on all 9 hard-coded positions in sequence |
| `BRAKE` | — | Stop drill motor immediately |
| `RPM` | — | Print current drill speed in RPM |
| `POS` | — | Print encoder position in pulses and degrees |
| `LOAD` | — | Print raw load cell reading |
| `HELP` | — | Print command reference |

> **Note on `UNSCREWCHAIN`:** The command currently ignores any coordinates passed to it and always runs the 9 hard-coded positions in `hardCodePoints[]`. This is a known bug — see [Known Issues](#known-issues).

### Example session

```
HOME
LOAD
> Load cell: 2154417.000
GOTO 233.5 195.0 140
UNSCREW 233.5 195.0
```

---

## Calibration

The `autoUnscrew` function relies on three load cell threshold constants that **must be measured and set for your specific setup**. The values in the current code are placeholders (`-450000.000`) and will not work reliably on a different installation.

```cpp
// In autoUnscrew() — set these before use
const float ENGAGE_LOAD           = -450000.000;  // load below which screw is considered touched
const float Z_UNSCREW_THRESHOLD   = -450000.000;  // load threshold to continue lowering during unscrew
const float DRILL_STOP_THRESHOLD  = -450000.000;  // load below which screw is considered released
```

**How to measure your thresholds:**

1. Run `HOME`, then `LOAD` to record baseline (unloaded) reading
2. Manually lower Z in small steps with `GOTO`, reading `LOAD` at each step until the tool contacts the screw head — note the value at first contact
3. Use `DRILL -90` in steps while reading `LOAD` between each to observe how load changes during unscrewing
4. Refer to the raw serial output recorded in Term 3 Week 7 progress notes for example values (~2.1M baseline, drops to ~1.6M as screw releases)

> **Important:** The load cell returns large positive integers, not Newtons. Do not compare these values to physical force units.

---

## autoUnscrew routine overview

```
Move to (X, Y, Z_START=140)
  → Lower Z in 0.5mm steps until load threshold reached
    → Drill CCW 720° to attempt engagement
      → Check load: if decreased, screw engaged
      → If not, retry drill 20° offset
        → Unscrew loop: drill CCW 180° + lower Z 0.2mm per step
          → Exit when count > 15 (or load drop detected)
            → Raise Z 30mm → move to deposit at (225, 310) → release
```

See the flowchart for a visual version.
<img width="439" height="806" alt="image" src="https://github.com/user-attachments/assets/1d34e39d-1efd-4b51-a1b6-d81468ff2ddc" />

---

## Known issues

| Issue | Description |
|---|---|
| `UNSCREWCHAIN` ignores parsed coordinates | The loop uses `hardCodePoints[]` regardless of input. Parsed `points[]` array is never used. |
| Exit condition is count-based | The unscrew loop exits after 15 drill pulses regardless of whether the screw is actually removed. Load-based exit (`prevLoad` comparison) is commented out. |
| All three thresholds are identical | `ENGAGE_LOAD`, `Z_UNSCREW_THRESHOLD`, and `DRILL_STOP_THRESHOLD` are all set to `-450000.000` — these need real measured values. |
| Magnetic tool head | Screws from electronics PCBs are often non-magnetic (brass, aluminium). The current magnetic bit cannot pick up or retain these. |
| Disposal coordinates hardcoded | Screw deposit position is hardcoded as `(225, 310)` rather than using the `SCREW_DISPOSAL_X/Y` defines already declared at the top of `main.ino`. |
| Several `#define` constants unused | `LOADCELL_THRESHOLD`, `LOADCELL_ENGAGEMENT_DEADBAND`, `SCREW_DISPOSAL_X/Y/Z`, and `STEPPER_INCREMENT` are defined but never referenced. |

---

## Recommended future development

1. **Migrate from Arduino to Raspberry Pi natively** — the Pi is currently only used as a serial terminal. Moving control logic onto the Pi directly would enable multithreading (parallel load cell monitoring + motor control), faster feedback loops, and easier integration with a vision system. Remove the Arduino and CNC shield layer entirely.

2. **Computer vision for screw detection** — the project previously explored YOLOv8 for screw detection. A fixed overhead camera with consistent lighting could replace the hard-coded coordinate array, allowing the robot to work on arbitrary hard drives without manual coordinate entry.

3. **Non-magnetic screw retention** — replace the magnetic bit with a vacuum pickup or compliant gripper that can retain non-magnetic screws (brass, aluminium). Electronics fasteners are frequently non-magnetic.

4. **Screw deposit box** — replace the current magnet-based deposit mechanism with a physical drop box or chute so screws are reliably collected regardless of material.

5. **Tune and harden the engagement logic** — replace the `count > 15` exit condition with a proper load-cell-based release detection. Implement a real retry loop for missed engagements with incremental bit rotation (e.g. 20° offset per retry).

---

## Project background

This is a university capstone engineering project (Robo Recycle). The goal is automated disassembly of e-waste — specifically hard drive lids — to recover materials and enable responsible recycling. The gantry is a repurposed Ultimaker 3D printer; the control system was written from scratch in Arduino C++ after evaluating GRBL and Universal G-Code Sender as alternatives.

---

## Repo structure

```
├── src/
│   ├── main.ino
│   ├── DCmotor.h / .cpp
│   ├── STEPPERmotor.h / .cpp
│   ├── Encoder.h / .cpp
│   └── Loadcell.h / .cpp
└── README.md
```

## 2024 github

https://github.com/AnujanCenan/Robo-Re-Cycle/blob/main/RaspToArdSerial.py

