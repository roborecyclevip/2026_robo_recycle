# Components And Wiring

This file lists the components that are clearly supported by the repository and the attached archive material.

## Sources Used

The component list below was assembled from:

- `System Integration/main/*.ino`, `*.cpp`, and `*.h`
- `System Integration/Unscrew.py`
- archived file `Robo-Recycle 2025 Report.docx`
- archived file `RoboRecycle_Handover  -  Repaired.pptx`

## Main Hardware Components

| Component | What it does | Evidence |
| --- | --- | --- |
| Repurposed Ultimaker frame | Provides the 3-axis gantry platform | README and handover deck |
| Arduino Mega 2560 | Main machine controller | Report pin map and Mega-only pin usage in code |
| Raspberry Pi or laptop | Sends serial commands over USB | `Unscrew.py`, README, handover deck |
| 3 stepper motors | Move X, Y, and Z axes | `STEPPERmotor.cpp` |
| Stepper drivers and CNC-style shield | Drive the stepper motors from Arduino step and dir pins | Handover deck and pin mapping in code |
| DC drill motor with encoder | Rotates the screwdriver bit and reports angle/speed | `DCmotor.cpp`, `Encoder.cpp`, project report |
| DC motor driver | Drives the drill motor from PWM and direction pins | `DCmotor.cpp`, project report |
| Load cell | Detects contact and unscrewing force changes | `Loadcell.cpp`, handover deck |
| HX711 amplifier | Reads the load cell | `Loadcell.h` and `Loadcell.cpp` |
| X, Y, Z end stops | Used for homing | `STEPPERmotor.cpp` |
| Magnetic bit adapter | Holds or transfers screws after removal | project report and handover deck |
| Drill chuck and spindle assembly | Mechanical tool head for the screw bit | project report |

## Specific Part Names Found In The Archive

These exact names appeared in the archived 2025 report:

| Part | Archive wording |
| --- | --- |
| Drill motor | `12V Metal DC Geared Motor with Encoder (131:1, 83RPM, 45Kg.cm)` |
| Drill motor SKU | `FIT0185` |
| Motor driver | `2x7A DC Motor Driver` |
| Motor driver SKU | `DRI0041` |
| Chuck | `B12 Electric Drill Chuck 1.5-10mm Clamp Taper with 6 mm Connecting Rod Sleeve` |
| Stepper motors | `MOONS MS17HD` series |

These are useful starting references, but still verify the physical hardware in your lab before ordering replacements.

## Controller Pin Map

The following pin map is directly supported by the current code.

### Drill motor driver

| Function | Arduino pin | Code location |
| --- | --- | --- |
| IN1 | 41 | `DCmotor.cpp` |
| IN2 | 43 | `DCmotor.cpp` |
| ENA PWM | 45 | `DCmotor.cpp` |

### Encoder

| Function | Arduino pin | Code location |
| --- | --- | --- |
| Channel A | 21 | `Encoder.cpp` |
| Channel B | 25 | `Encoder.cpp` |

### Load cell amplifier

| Function | Arduino pin | Code location |
| --- | --- | --- |
| HX711 DOUT | A14 | `Loadcell.h` |
| HX711 SCK | A15 | `Loadcell.h` |

### Stepper axes and end stops

| Axis | STEP pin | DIR pin | End stop pin | Code location |
| --- | --- | --- | --- | --- |
| X | 2 | 5 | 10 | `STEPPERmotor.cpp` |
| Y | 3 | 6 | 9 | `STEPPERmotor.cpp` |
| Z | 4 | 7 | 11 | `STEPPERmotor.cpp` |

## Software Components

| Software piece | Purpose | Included in repo |
| --- | --- | --- |
| `main.ino` | Main Arduino firmware | Yes |
| `DCmotor.*` | Drill motor control | Yes |
| `Encoder.*` | Encoder position and RPM tracking | Yes |
| `Loadcell.*` | HX711 load-cell wrapper | Yes |
| `STEPPERmotor.*` | Homing and X/Y/Z motion | Yes |
| `Unscrew.py` | Sends repeated `UNSCREW` commands over serial | Yes |
| `HX711` library | External Arduino dependency | No |
| `MultiStepperLite` library | External Arduino dependency | No |
| `pyserial` | Python serial library | No |

## What The System Is Not Using Yet

These ideas appear in the archive, but they are not active in the current repo:

- computer vision for automatic screw detection
- native Raspberry Pi motion control
- a non-magnetic screw pickup solution
- a proper screw drop box or chute

## Important Unknowns To Verify In The Lab

The repo and archive do not clearly lock down every detail. Confirm these physically before making changes:

- exact CNC shield model
- exact stepper driver model
- exact load-cell model and capacity
- power supply ratings and wiring
- final spindle assembly dimensions
- whether the current machine still matches the 2025 report hardware

## Practical Summary For New Students

If you are standing in front of the machine and wondering what matters most, this is the short version:

- Arduino Mega is the real controller
- Raspberry Pi is just the command sender
- stepper motors move the gantry
- the DC motor spins the screw bit
- the encoder tells the code how far the drill rotated
- the load cell helps detect screw contact and release
- end stops define home position
