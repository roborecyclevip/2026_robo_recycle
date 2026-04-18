# Robo Recycle Task Roadmap

This roadmap tracks the near-term migration from an Arduino-centered prototype toward a Raspberry Pi terminal-controlled system. The current direction is to keep the Arduino and CNC shield for gantry motion while moving sensing, orchestration, and future computer vision work onto the Raspberry Pi.

## Architecture Goal

The Raspberry Pi should become the main controller for the robot workflow:

- send gantry commands to the Arduino/CNC shield over serial
- read and display live force/load data
- coordinate drill commands, Z movement, screw engagement checks, and recovery steps
- provide a terminal interface for testing and operation
- later accept computer vision results in place of load-cell-based decisions

The Arduino should gradually become a lower-level device. In the first migration stage it still controls the CNC shield and steppers. If the drill motor is moved to the Pi through a suitable motor driver, the Arduino can eventually be isolated to only the motion role that is still needed, or removed/replaced later if a dedicated motion controller is adopted.

## Clarifying Note: Replaceable Screw State Logic

Create a software boundary between sensing and actuation. The robot should not hard-code "load cell value means screw state" directly inside drill or gantry code. Instead, define a replaceable screw-state interface that can answer questions such as:

- Has the tool contacted the screw?
- Is the bit engaged with the screw head?
- Has the screw released?
- Should Z continue lowering, hold position, or retract?

For now, that interface can be backed by the load cell. Later, the same interface can be backed by a computer vision system, or by a hybrid of vision plus force feedback. This keeps the load cell from becoming a permanent architectural dependency.

## Tasks

1. **Fix Raspberry Pi serial baud rate**
   - Update Raspberry Pi Python serial scripts from `9600` baud to `115200` baud to match the Arduino firmware.
   - Verify `HELP`, `HOME`, `GOTO`, `LOAD`, `DRILL`, and `BRAKE` commands respond consistently.
   - Add one shared serial config constant so future scripts do not drift out of sync.

2. **Move load sensor reading onto the Raspberry Pi**
   - Wire the load cell/HX711 path to the Raspberry Pi, or choose a Pi-compatible ADC/load-cell interface if the existing wiring cannot be reused directly.
   - Build a small Pi-side load-cell module that can tare, read raw values, smooth readings, and report calibrated/uncalibrated force values.
   - Remove the load-cell decision logic from Arduino `autoUnscrew` once the Pi can make those decisions.
   - Keep the Arduino/CNC shield responsible for gantry movement during this stage.

3. **Create a Raspberry Pi terminal control program**
   - Build one terminal UI/CLI that can connect to the Arduino, send commands, and show machine status.
   - Include live force display while the machine is idle or moving.
   - Include manual controls for homing, jogging/moving XYZ, drilling, braking, reading RPM/position, and running an unscrew sequence.
   - Make command output timestamped and easy to log for debugging.

4. **Split high-level unscrew sequencing from low-level movement**
   - Move the unscrew state machine to the Raspberry Pi.
   - Keep Arduino commands simple: move to position, home, drill, brake, report position/status.
   - Replace Arduino-side blocking `autoUnscrew` with Pi-side steps that can monitor force continuously between movement/drill commands.
   - Add clear abort conditions for overload, timeout, endstop fault, serial disconnect, and emergency stop.

5. **Define the replaceable screw-state interface**
   - Create a Pi-side module such as `ScrewStateProvider` or `EngagementDetector`.
   - First implementation: load-cell-based screw contact, engagement, and release detection.
   - Future implementation: computer-vision-based screw detection and state estimation.
   - Keep drill and gantry code dependent on this interface, not on load-cell-specific variables.

6. **Investigate moving drill motor control to the Raspberry Pi**
   - Identify the drill motor voltage, current, stall current, encoder wiring, and required direction/speed control.
   - Select a suitable motor driver or H-bridge between the Pi and drill motor.
   - Confirm whether the Pi can read the drill encoder reliably, or whether a small microcontroller should remain responsible for encoder counting.
   - Add electrical protection notes: common ground, level shifting, flyback/noise handling, fusing, and emergency stop behavior.

7. **Create a hardware pinout and wiring document**
   - Document Arduino/CNC shield stepper pins, endstop pins, drill driver pins, encoder pins, load-cell pins, and Raspberry Pi GPIO pins.
   - Mark which wires are currently connected and which are planned to move.
   - Add photos or diagrams once the physical wiring is stable.

8. **Add a staged test plan**
   - Test serial-only command flow with motors disabled.
   - Test homing and each axis independently.
   - Test live force display without movement.
   - Test force display during slow Z movement.
   - Test drill motor control separately from gantry movement.
   - Test one full screw cycle at low speed with manual abort ready.
   - Record expected output and failure symptoms for each test.

9. **Add safety and reliability controls**
   - Add a physical emergency stop path that removes motor power.
   - Add a software `ABORT` command that brakes the drill and stops the current sequence.
   - Add travel limits and sanity checks before executing any Pi-generated move.
   - Add serial reconnect handling so the terminal program fails safely.

10. **Prepare for computer vision integration**
    - Define the data that vision must output, such as screw coordinates, confidence, screw state, and target approach point.
    - Keep hard-coded screw coordinates available as a fallback mode.
    - Add a simulation/mock provider so vision can be developed without moving the real gantry.
    - Decide how calibration will map camera pixels to gantry coordinates.

11. **Improve project configuration and documentation**
    - Move shared constants such as baud rate, serial port, safe Z height, screw disposal position, and movement limits into config files.
    - Document Raspberry Pi setup steps and Python dependencies.
    - Add a short operator checklist for startup, homing, testing force readings, and shutdown.

12. **Revisit motion-controller options after the Pi orchestration works**
    - Keep the Arduino/CNC shield path working first.
    - Once the Pi-side orchestration and sensing layers are stable, compare staying on Arduino/CNC shield versus moving to FluidNC or another dedicated motion controller.
    - Use actual test results, missed steps, wiring complexity, and reliability as the decision criteria.

## Suggested First Milestone

Complete tasks 1 to 3 first. At that point the Raspberry Pi should be able to operate the current machine from a terminal and show live force readings, while the Arduino/CNC shield still handles gantry movement. That gives a clean base for moving the unscrew logic out of Arduino code.

