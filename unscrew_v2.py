#!/usr/bin/env python3
"""Run with python3 unscrew_v2.py from the project directory."""

from unscrew_v2_helper import (
    align_tool,
    brake_drill,
    connect_arduino,
    drop_screw_at_magnet,
    detect_screw_engagement,
    home,
    move_to,
    read_screw_coordinates,
    rotate_drill,
)


# Edit the sequence settings here. Increasing Z lowers the tool.
USE_CAMERA = True
CAMERA_SCANNING_Z = 200.0
SAFE_Z = 190.0
ALIGNMENT_Z = 200.0  # Hover above the HDD while aligning the tool.
FINE_ALIGNMENT_Z = 205.0
TARGET_Z = 207.0
# Do not enable preload until independent safe travel limits are verified.
PRELOAD_MM = 0.0
ENGAGEMENT_SPEED = -180
ENGAGEMENT_FINISH_MS = 3000

# Start with a slow turn, then speed up for the remaining turns.
TURN_SPEEDS = (20, 50, 50, 50, 50, 50, 50, 50, 50, 50, 50)
THREAD_RISE_PER_TURN_MM = 0.5 # 1 for M6, 0.5 for T8
TOTAL_CLIMB_MM = 5 # 20 for M6, 7 for T8


def unscrew(connection, x, y):
    """Align at screw position (x, y), remove the screw and drop it at the magnet. Returns None."""
    # Check the camera position at the hover height before lowering further.
    move_to(connection, x, y, SAFE_Z)
    move_to(connection, x, y, ALIGNMENT_Z)
    print(f"Coarse alignment at Z{ALIGNMENT_Z:g}. Finish when the bit is over the screw.")
    x, y = align_tool(connection, x, y, ALIGNMENT_Z)

    # Lower at the corrected XY position and make the finer adjustments there.
    move_to(connection, x, y, FINE_ALIGNMENT_Z)
    print(f"Fine alignment at Z{FINE_ALIGNMENT_Z:g}. Finish when the bit is lined up.")
    x, y = align_tool(connection, x, y, FINE_ALIGNMENT_Z)

    print("Starting automatic current/RPM engagement detection...")
    result, detected_z = detect_screw_engagement(
        connection, x, y, TARGET_Z,
        speed=ENGAGEMENT_SPEED,
        finish_ms=ENGAGEMENT_FINISH_MS,
    )
    if result != "DETECTED":
        print(f"Engagement unsuccessful: {result}. No further motion commanded.")
        raise RuntimeError(f"Engagement failed: {result}; operator recovery required")

    print(f"Engagement signal detected at Z={detected_z:.3f} mm")
    answer = input("Confirm bit seated: Enter to unscrew, S to stop: ").strip().upper()
    if answer:
        raise RuntimeError("Operator stopped after detection; inspect before moving")

    start_z = detected_z + PRELOAD_MM
    if start_z > TARGET_Z + 0.001:
        raise RuntimeError("Preload exceeds engagement search limit")
    if PRELOAD_MM:
        move_to(connection, x, y, start_z)

    # Let the compliance take up each turn, then raise by the thread's rise.
    z = start_z
    for speed in TURN_SPEEDS:
        rotate_drill(connection, turns=1, speed=speed)
        z -= THREAD_RISE_PER_TURN_MM
        move_to(connection, x, y, z)

    # Complete the 5 mm climb from the preloaded position before retracting.
    brake_drill(connection)
    move_to(connection, x, y, start_z - TOTAL_CLIMB_MM)
    drop_screw_at_magnet(connection, x, y, SAFE_Z)


def main():
    """Home, load the screw positions and run the routine for each one. Takes no inputs and returns None."""
    with connect_arduino() as connection:
        home(connection)
        if USE_CAMERA:
            move_to(connection, 0, 0, CAMERA_SCANNING_Z)

        coordinates = read_screw_coordinates(USE_CAMERA)
        print("Screw coordinates:", coordinates)
        move_to(connection, 0, 0, SAFE_Z)

        for x, y in coordinates:
            unscrew(connection, x, y)
        print("All screws done.")


if __name__ == "__main__":
    main()
