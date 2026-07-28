#!/bin/python3
#
# This prog runs the random gantry test described in the slides.
# It redraws the same 5 random coordinates 5 times so that we can
# compare how close the dots are to each other.

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

def draw_dot(ser, prev_x, prev_y, x_coor, y_coor, z_coor):
    # First raise up from the previous dot.
    send_command(ser, f"GOTO {prev_x} {prev_y} {z_coor - RAISE_DISTANCE}")

    # Move above the next coordinate, then move down to draw the dot.
    send_command(ser, f"GOTO {x_coor} {y_coor} {z_coor - RAISE_DISTANCE}")
    send_command(ser, f"GOTO {x_coor} {y_coor} {z_coor}")

# Runs assuming z_coor is where pen touches paper
def run_gantry_random_test(ser, z_coor):
    print(
        f"Drawing {len(RANDOM_COORDINATES)} coordinates "
        f"{NUMBER_OF_REPEATS} times at z of {z_coor}"
    )

    # Home once at the beginning so that all coordinates have a known reference.
    send_command(ser, "HOME")
    prev_x = 0
    prev_y = 0

    for repeat in range(NUMBER_OF_REPEATS):
        print(f"Starting repeat {repeat + 1} of {NUMBER_OF_REPEATS}")

        for x_coor, y_coor in RANDOM_COORDINATES:
            draw_dot(ser, prev_x, prev_y, x_coor, y_coor, z_coor)
            prev_x = x_coor
            prev_y = y_coor

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

        run_gantry_random_test(ser, z_coor)
    finally:
        ser.close()
        print("Serial connection closed.")


if __name__ == "__main__":
    main()
