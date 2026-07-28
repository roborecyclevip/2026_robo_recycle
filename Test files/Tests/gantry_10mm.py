#!/bin/python3
#
# This prog just runs the 10 mm gantry test described 
# in the slides

import serial
import time
import sys
import readline

from serial_config import BAUD_RATE, SERIAL_PORT

def send_command(ser, cmd):
    cmd_str = cmd + '\n'          # Add newline as Arduino expects
    ser.write(cmd_str.encode())   # Send bytes
    time.sleep(0.1)               # Wait for Arduino to process

    # Read any available response
    while ser.in_waiting:
        response = ser.readline().decode(errors='ignore').strip()
        if response:
            print("Arduino:", response)

# Runs assuming z_coor is where pen touches paper
def run_10_mm_accuracy_test(ser, z_coor):
    print(f"We are attempting the 10mm test from 20 x 20 mm to 220 x 220 mm at z of {z_coor}")

    # Previous coordinates used to make travel into a process
    # of UP, FORWARD, DOWN. Like a claw machine.
    prev_x = 20
    prev_y = 20
    for x_coor in range(20, 220, 10):
        for y_coor in range(20, 220, 10):
            # First raise yourself up from old position
            send_command(ser, f"GOTO {prev_x}  {prev_y} {z_coor - 50}") # 50 is arbitrary
            # Then move to next position
            send_command(ser, f"GOTO {x_coor}  {y_coor} {z_coor - 50}")
            # Then go down to make your drop
            send_command(ser, f"GOTO {x_coor}  {y_coor} {z_coor}")

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
        print("Before beginning what should the z coordinate be for the gantry to touch the paper? ") 
        try:
            z_coor = float(input())
        except ValueError:
            print("ValueError: Check if it's a valid decimel", file=sys.stderr)
            return

        run_10_mm_accuracy_test(ser, z_coor)
    finally:
        ser.close()
        print("Serial connection closed.")

if __name__ == "__main__":
    main()
