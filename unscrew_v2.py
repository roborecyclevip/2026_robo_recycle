#!/usr/bin/env python3
# Run with: python3 unscrew_v2.py
# Like unscrew.py, but the Pi runs the removal steps inside unscrew(x, y).
# Arduino only handles HOME, GOTO, DRILL and BRAKE.

import csv
from pathlib import Path
import time
import readline # This should help with the whole shell read

# SETTINGS: edit these values to change how the routine runs.
SERIAL_PORT = "/dev/ttyACM0"
BAUD_RATE = 115200
USE_CAMERA = True        # Like unscrew.py: find fresh screws before removal
COORDINATES_CSV = Path(__file__).resolve().parent / "coordinates.csv"

# Position of the CSV's reference dot relative to the gantry origin, in mm.
X_OFFSET = 99.8
Y_OFFSET = 98.5
# Goto z 119 to see if it's on the dot :P

# 113.2, 110.2, 105

# Increasing Z moves DOWN; decreasing Z moves UP. All distances are in mm.
CONTACT_Z = 111.0
SAFE_Z = 80.0
APPROACH_CLEARANCE = 2.0  # Start contact checking at Z=109 with these settings
Z_STEP = 0.5
ALIGNMENT_STEP = 0.1

# Each pass stops the drill before asking whether the screw is free.
DRILL_DEGREES = -180     # Negative degrees means reverse
DRILL_SPEED = 180        # Positive PWM speed: 1 to 255
Z_CLIMB_PER_TURN = 0.8   # Rise this many mm for each 360 degrees of unscrewing

# Drop-off positions from the existing Arduino routine.
SCREW_DROPOFF_X = 320.0
SCREW_DROPOFF_Y = 220.0
SCREW_DROPOFF_APPROACH_Y = 200.0

# One shared connection, like unscrew.py
import serial
ser = serial.Serial(SERIAL_PORT, BAUD_RATE, timeout=1, write_timeout=2)
time.sleep(2)  # Give Arduino time to reset after opening USB, like unscrew.py


# COORDINATE OFFSET: convert positions measured from the dot to gantry positions.

def offset_coordinates(x, y):
    """
    Add the reference dot's position to one CSV coordinate pair.
    Inputs: x and y are distances from the reference dot, in millimetres.
    Output: (x, y) in gantry coordinates, with X_OFFSET and Y_OFFSET added.
    """
    return x + X_OFFSET, y + Y_OFFSET


# COMMAND HELPERS: send commands and display the Arduino replies.

def send_command(cmd):
    """
    Send a command and print Arduino replies until the command finishes.
    Inputs: cmd is the command text, such as HOME or GOTO 100 100 80.
    Output: None. Prints replies until the completion message arrives.

    """
    # These are the completion messages printed by main.ino.
    completion_messages = {
        "HOME": "Homed.",
        "GOTO": "Move complete.",
        "DRILL": "Done.",
        "BRAKE": "Drill stopped.",
    }
    command_name = cmd.split()[0].upper()
    expected = completion_messages.get(command_name)

    ser.write((cmd + "\n").encode())
    print("Sent:", cmd)

    # Keep reading even when no bytes have arrived yet. readline waits up to
    # the serial timeout; an empty reply means we should keep waiting.
    while True:
        response = ser.readline().decode(errors="replace").strip()
        if not response:
            continue
        print("Arduino:", response)
        if response == expected or expected is None:
            return

def move_to(x, y, z):
    """
    Send GOTO and print replies until Move complete.
    Inputs: x, y, z are the absolute destination in millimetres.
    Output: None.

    """
    send_command(f"GOTO {x:.3f} {y:.3f} {z:.3f}")


# MANUAL INPUT: answers stay on the Pi instead of being sent to Arduino.

def ask_manual(prompt, valid_answers, default=""):
    """
    Read one manual action. Enter uses the default action when one is supplied.
    Inputs: prompt, accepted words, and an optional default word.
    Output: an accepted word in uppercase. Use Ctrl+C to stop the script.

    """
    while True:
        answer = input(prompt + ": ").strip().upper()
        if not answer:
            answer = default
        shortcuts = {"Y": "YES", "N": "NO", "A": "AGAIN", "U": "UP", "D": "DOWN", "S": "STOP", ".": "DONE"}
        answer = shortcuts.get(answer, answer)
        if answer in valid_answers:
            return answer
        print("Please enter one of:", ", ".join(valid_answers))


# Inputs: prompt, allowed directions, default step in mm, and the previous move.
# Output: (direction, distance), for example ("FORWARD", 2.0), or ("DONE", 0).
# Purpose: accept a short move such as F 2, or Enter to repeat the last move.
def ask_adjustment(prompt, valid_directions, step, previous_move):
    while True:
        answer = input(prompt + ": ").strip().upper()
        if not answer:
            return previous_move

        words = answer.split()
        shortcuts = {"F": "FORWARD", "B": "BACKWARD", "L": "LEFT", "R": "RIGHT", "U": "UP", "D": "DOWN", ".": "DONE"}
        direction = shortcuts.get(words[0], words[0])
        if direction == "DONE":
            return "DONE", 0
        if direction in valid_directions:
            distance = step
            if len(words) > 1:
                distance = float(words[1])  # Optional distance is in mm, not steps
            return direction, distance
        print("Use", "/".join(valid_directions), "or DONE. Example: a direction followed by 2 for 2 mm.")


# UNSCREW ROUTINE: edit the steps here to change how one screw is removed.

def unscrew(x, y):
    """
    align, find contact, drill in passes, lift and drop off one screw.
    Inputs: x and y are the screw coordinates in millimetres.
    Output: None. Runs one screw cycle using the operator's answers.

    """
    # 1. Move above the screw at the travelling height.
    move_to(x, y, SAFE_Z)

    # 2. Nudge X/Y until the bit is lined up.
    # FORWARD is +Y, BACKWARD is -Y, LEFT is -X, RIGHT is +X.
    # F/B/L/R is one small step; F 2 moves 2 mm in one command.
    # Enter repeats the previous move. Before any move, Enter finishes alignment.
    previous_move = ("DONE", 0)
    while True:
        answer, distance = ask_adjustment("Align: F/B/L/R [mm], Enter repeat, DONE finish", ("FORWARD", "BACKWARD", "LEFT", "RIGHT"), ALIGNMENT_STEP, previous_move)
        if answer == "DONE":
            break
        if answer == "FORWARD":
            y += distance
        elif answer == "BACKWARD":
            y -= distance
        elif answer == "LEFT":
            x -= distance
        elif answer == "RIGHT":
            x += distance
        move_to(x, y, SAFE_Z)
        previous_move = (answer, distance)

    # 3. Approach just above the expected contact height.
    z = CONTACT_Z - APPROACH_CLEARANCE
    move_to(x, y, z)

    # 4. Adjust Z directly. DONE means the bit is touching and engaged.
    # Enter initially lowers one Z_STEP, then repeats the last UP/DOWN move.
    previous_move = ("DOWN", Z_STEP)
    while True:
        answer, distance = ask_adjustment("Contact: U/D [mm], Enter repeat, DONE engaged", ("UP", "DOWN"), Z_STEP, previous_move)
        if answer == "DONE":
            break
        if answer == "UP":
            z -= distance
        else:
            z += distance
        move_to(x, y, z)
        previous_move = (answer, distance)

    # 5. Enter runs one drill pass; DONE means the screw has come free.
    # U/D adjusts Z without drilling; STOP ends this screw and raises the bit.
    while True:
        answer = ask_manual("Unscrew: Enter next pass, DONE removed, U/D adjust, STOP", ("AGAIN", "DONE", "UP", "DOWN", "STOP"), default="AGAIN")
        if answer == "DONE":
            break
        if answer == "STOP":
            send_command("BRAKE")
            move_to(x, y, SAFE_Z)
            return
        if answer == "UP":
            z -= Z_STEP
            move_to(x, y, z)
        elif answer == "DOWN":
            z += Z_STEP
            move_to(x, y, z)
        else:
            send_command(f"DRILL {DRILL_DEGREES} {DRILL_SPEED}")
            # Rise after the completed rotation. Smaller Z moves the bit UP.
            # -180 degrees rises 0.4 mm; -360 rises 0.8 mm; -90 rises 0.2 mm.
            # climb = Z_CLIMB_PER_TURN * abs(DRILL_DEGREES) / 360.0
            # z -= climb
            move_to(x, y, z)

    # 6. Lift vertically before moving sideways.
    send_command("BRAKE")
    move_to(x, y, SAFE_Z)

    # 7. Carry the screw through the approach point to the drop-off point.
    move_to(SCREW_DROPOFF_X, SCREW_DROPOFF_APPROACH_Y, SAFE_Z)
    move_to(SCREW_DROPOFF_X, SCREW_DROPOFF_Y, 120)
    while True:
        answer = ask_manual("Screw off the bit? Enter YES, or N to wait", ("YES", "NO"), default="YES")
        if answer == "YES":
            break
        print("Clear the screw before continuing.")
    move_to(SCREW_DROPOFF_X, SCREW_DROPOFF_APPROACH_Y, SAFE_Z)


# MAIN PROGRAM: home, get coordinates, then call unscrew(x, y) for each screw.

def main():
    """
    run the same overall workflow as unscrew.py using the Pi's routine.
    Inputs: none; uses the settings, CSV and manual answers above.
    Output: None. Prints the result and closes serial when the job ends.

    """

    # Home before taking the camera image, just like unscrew.py.
    send_command("HOME")
    if USE_CAMERA:
        # The existing finder expects to run from the project directory.
        from find_screws import find_screws
        find_screws()

    # Read the screw coordinates from the CSV.
    coordinates_to_unscrew = []
    with open(COORDINATES_CSV, newline="", encoding="utf-8-sig") as file:
        next(file, None)  # Skip the x_coord,y_coord header

        for row in csv.reader(file):
            # Apply the dot offset once, as each coordinate is read from CSV.
            x, y = offset_coordinates(float(row[0]), float(row[1]))
            coordinates_to_unscrew.append((x, y))

    print("Got these coordinates:\n", coordinates_to_unscrew)

    # HOME leaves XYZ at zero. Set travelling height before any XY move.
    move_to(0, 0, SAFE_Z)
    for x, y in coordinates_to_unscrew:
        unscrew(x, y)
    print("All screws done.")


    send_command("BRAKE")
    ser.close()
    print("Serial connection closed.")


if __name__ == "__main__":
    main()
