"""Serial, camera, alignment and drop-off helpers for unscrew_v2.py."""

import csv
from pathlib import Path
import time
import readline  # Enable editing and history at the input prompts.


SERIAL_PORT = "/dev/ttyACM0"
BAUD_RATE = 115200
COORDINATES_CSV = Path(__file__).resolve().parent / "coordinates.csv"

# Convert camera coordinates to gantry coordinates using the current dot offsets.
X_OFFSET = -2.0
Y_OFFSET = 13.0
ALIGNMENT_STEP = 0.1

# Positive command value for one physical turn in the unscrewing direction.
DRILL_UNITS_PER_TURN = 1600
MAGNET_X, MAGNET_Y, MAGNET_Z = 205.0, 145.0, 215.0


def connect_arduino():
    """Open the Arduino connection and allow it to reset. Takes no inputs and returns the connection."""
    import serial

    connection = serial.Serial(SERIAL_PORT, BAUD_RATE, timeout=1, write_timeout=2)
    time.sleep(2)
    return connection


def send_command(connection, command, completion):
    """Send command text over connection and print replies through the completion line. Returns None."""
    connection.write((command + "\n").encode())
    print("Sent:", command)
    while True:
        reply = connection.readline().decode(errors="replace").strip()
        if reply:
            print("Arduino:", reply)
        if reply == completion:
            return


def home(connection):
    """Home the gantry through the Arduino connection. Returns None when HOME finishes."""
    send_command(connection, "HOME", "Homed.")


def move_to(connection, x, y, z):
    """Move to absolute X, Y and Z in mm through connection. Returns None when the move finishes."""
    send_command(connection, f"GOTO {x:.3f} {y:.3f} {z:.3f}", "Move complete.")


def rotate_drill(connection, turns, speed):
    """Unscrew by the given number of physical turns at the given PWM speed. Returns None when done."""
    command_angle = turns * DRILL_UNITS_PER_TURN
    send_command(connection, f"DRILL {command_angle:g} {speed}", "Done.")


def brake_drill(connection):
    """Send the normal BRAKE command through connection. Returns None after the Arduino replies."""
    send_command(connection, "BRAKE", "Drill stopped.")


def read_screw_coordinates(use_camera):
    """Refresh the CSV if use_camera is true, then return its screw positions as gantry (x, y) pairs."""
    if use_camera:
        from find_screws import find_screws

        find_screws()

    coordinates = []
    with COORDINATES_CSV.open(newline="", encoding="utf-8-sig") as file:
        next(file, None)  # Skip the header.
        for x, y in csv.reader(file):
            coordinates.append((float(x) + X_OFFSET, float(y) + Y_OFFSET))
    return coordinates


def align_tool(connection, x, y, z):
    """Nudge the tool from the supplied XYZ position. Return the final (x, y) for unscrewing."""
    # A smaller Z raises the tool, and a larger Z lowers it.
    directions = {
        "F": (0, 1, 0), "FORWARD": (0, 1, 0),
        "B": (0, -1, 0), "BACKWARD": (0, -1, 0),
        "L": (-1, 0, 0), "LEFT": (-1, 0, 0),
        "R": (1, 0, 0), "RIGHT": (1, 0, 0),
        "U": (0, 0, -1), "UP": (0, 0, -1),
        "D": (0, 0, 1), "DOWN": (0, 0, 1),
    }
    last_dx, last_dy, last_dz = 0, 0, 0
    while True:
        words = input("Align: F/B/L/R/U/D [mm], Enter repeat, DONE finish: ").strip().upper().split()
        if words and words[0] in ("DONE", "."):
            return x, y
        if words:
            direction = words[0]
            if direction not in directions:
                print("Use F, B, L, R, U or D, optionally followed by a distance in mm.")
                continue
            try:
                distance = float(words[1]) if len(words) > 1 else ALIGNMENT_STEP
            except ValueError:
                print("Enter a distance in mm, for example F 2.")
                continue
            dx, dy, dz = directions[direction]
            last_dx, last_dy, last_dz = dx * distance, dy * distance, dz * distance
        elif last_dx == last_dy == last_dz == 0:
            return x, y

        x += last_dx
        y += last_dy
        z += last_dz
        move_to(connection, x, y, z)


def drop_screw_at_magnet(connection, x, y, safe_z):
    """From screw position (x, y), lift, visit the magnet and lift again. Returns None."""
    move_to(connection, x, y, safe_z)
    move_to(connection, MAGNET_X, MAGNET_Y, safe_z)
    move_to(connection, MAGNET_X, MAGNET_Y, MAGNET_Z)
    input("Press Enter when the screw is off the bit: ")
    move_to(connection, MAGNET_X, MAGNET_Y, safe_z)
