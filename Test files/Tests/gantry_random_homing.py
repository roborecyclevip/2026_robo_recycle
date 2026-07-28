#!/bin/python3
#
# This is the same random test as gantry_random.py, except the gantry
# homes again before travelling to every coordinate.

import serial
import time
import sys

from serial_config import BAUD_RATE, SERIAL_PORT


# These coordinates stay the same for every run of the test.
RANDOM_COORDINATES = [
    (35, 70),
    (75, 190),
    (120, 110),
    (165, 45),
    (205, 175),
]

NUMBER_OF_REPEATS = 5
RAISE_DISTANCE = 50


def send_command(ser, cmd):
    cmd_str = cmd + '\n'          # Add newline as Arduino expects
    ser.write(cmd_str.encode())   # Send bytes
    time.sleep(0.1)               # Wait for Arduino to process

    # Read any available response
    while ser.in_waiting:
        response = ser.readline().decode(errors='ignore').strip()
        if response:
            print("Arduino:", response)


def home_and_draw_dot(ser, x_coor, y_coor, z_coor):
    # Re-home before travelling to this coordinate.
    send_command(ser, "HOME")

    # Move above the coordinate, then move down to draw the dot.
    send_command(ser, f"GOTO {x_coor} {y_coor} {z_coor - RAISE_DISTANCE}")
    send_command(ser, f"GOTO {x_coor} {y_coor} {z_coor}")

# Runs assuming z_coor is where pen touches paper
def run_gantry_random_homing_test(ser, z_coor):
    print(
        f"Drawing {len(RANDOM_COORDINATES)} coordinates "
        f"{NUMBER_OF_REPEATS} times at z of {z_coor}, homing before every dot"
    )

    for repeat in range(NUMBER_OF_REPEATS):
        print(f"Starting repeat {repeat + 1} of {NUMBER_OF_REPEATS}")

        for x_coor, y_coor in RANDOM_COORDINATES:
            home_and_draw_dot(ser, x_coor, y_coor, z_coor)


def main():
    try:
        ser = serial.Serial(SERIAL_PORT, BAUD_RATE, timeout=1)
        time.sleep(2)  # Wait for Arduino to reset after connection
    except serial.SerialException:
        print(f"Could not open serial port {SERIAL_PORT}")
        return

    try:
        print("Before beginning what should the z coordinate be for the gantry to touch the paper?")

        try:
            z_coor = float(input())
        except ValueError:
            print("ValueError: Check if it's a valid decimal", file=sys.stderr)
            return

        run_gantry_random_homing_test(ser, z_coor)
    finally:
        ser.close()
        print("Serial connection closed.")


if __name__ == "__main__":
    main()
