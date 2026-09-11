#!/bin/python3
#
# This prog just runs the 20 mm gantry test described 
# in the slides.
# Currently the test just drops dots and we will see how close they are
# The test does not clearly differentiate dots

import serial
import time
import sys
import readline

from serial_config import BAUD_RATE, SERIAL_PORT
from enum import Enum

# Constants
class DIRECTION(Enum): # My best attempt at an ENUM
    BEHIND = 1
    FRONT = 2
    LEFT = 3
    RIGHT = 4

def send_command(ser, cmd):
    cmd_str = cmd + '\n'          # Add newline as Arduino expects
    ser.write(cmd_str.encode())   # Send bytes
    time.sleep(0.1)               # Wait for Arduino to process

    # Read any available response
    while ser.in_waiting:
        response = ser.readline().decode(errors='ignore').strip()
        if response:
            print("Arduino:", response)

# direction is some constant DIRECTION defined at the top
# Behind == lower x_coor
# Front == upper x_coor
# left == y_coor
# right == y_coor
def approach_from_direction_and_dot(ser, direction: DIRECTION, x_coor: float, y_coor: float, z_coor: float):
    # Go home to reset all values / use end stops to re-set reference
    send_command(ser, f"HOME")

    # Depending on the direction, we go to different areas
    if direction == DIRECTION.FRONT.value:    
        # Go to the extreme edge before travelling to the coordinate
        send_command(ser, f"GOTO 220 {y_coor} {z_coor - 50}")
    if direction == DIRECTION.BEHIND.value:    
        # Go to the extreme edge before travelling to the coordinate
        send_command(ser, f"GOTO 0 {y_coor} {z_coor - 50}")
    if direction == DIRECTION.LEFT.value:    
        # Go to the extreme edge before travelling to the coordinate
        send_command(ser, f"GOTO {x_coor} 0 {z_coor - 50}")
    if direction == DIRECTION.RIGHT.value:
        # Go to the extreme edge before travelling to the coordinate
        send_command(ser, f"GOTO {x_coor} 220 {z_coor - 50}")

    # Then move to next position
    send_command(ser, f"GOTO {x_coor}  {y_coor} {z_coor - 50}")
    # Then go down to make your drop
    send_command(ser, f"GOTO {x_coor}  {y_coor} {z_coor}")

# Runs assuming a particular z_coordinate that is the z-level for pen touching papge
def run_gantry_diff_direction_test(ser, z_coor):
    print(f"We are attempting the multi directional approach at any singular dot z of {z_coor}")

    # Previous coordinates used to make travel into a process
    # of UP, FORWARD, DOWN. Like a claw machine.
    for x_coor in range(20, 220, 40):
        for y_coor in range(20, 220, 40):
            approach_from_direction_and_dot(ser, DIRECTION.FRONT.value, x_coor, y_coor, z_coor)
            approach_from_direction_and_dot(ser, DIRECTION.BEHIND.value, x_coor, y_coor, z_coor)
            approach_from_direction_and_dot(ser, DIRECTION.LEFT.value, x_coor, y_coor, z_coor)
            approach_from_direction_and_dot(ser, DIRECTION.RIGHT.value, x_coor, y_coor, z_coor)

def main():
    try:
        ser = serial.Serial(SERIAL_PORT, BAUD_RATE, timeout=1)
        time.sleep(2)  # Wait for Arduino to reset after connection
    except serial.SerialException:
        print(f"Could not open serial port {SERIAL_PORT}")
        return

    try:
        print("Before beginning what should the z coordinate be for the gantry to touch the paper? ") 
        try:
            z_coor = float(input())
        except ValueError:
            print("ValueError: Check if it's a valid decimel", file=sys.stderr)
            return

        run_gantry_diff_direction_test(ser, z_coor)
    finally:
        ser.close()
        print("Serial connection closed.")

if __name__ == "__main__":
    main()
