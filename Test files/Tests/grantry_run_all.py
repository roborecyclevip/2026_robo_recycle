#!/bin/python3
#
# This prog runs all of the gantry tests with one serial connection.
# It asks for the z coordinate once and waits for the paper to be
# changed before starting the next test.

import serial
import time
import sys
from pathlib import Path

# serial_config.py is in the directory above the Tests directory.
sys.path.append(str(Path(__file__).resolve().parent.parent))

from serial_config import BAUD_RATE, SERIAL_PORT

import gantry_20mm
import gantry_10mm
import gantry_random
import gantry_random_homing
import gantry_diff_direction


# Each entry uses the test function that already exists in its script.
TESTS = [
    ("20 mm accuracy test", gantry_20mm.run_20_mm_accuracy_test),
    ("10 mm accuracy test", gantry_10mm.run_10_mm_accuracy_test),
    ("random coordinate test", gantry_random.run_gantry_random_test),
    ("random coordinate homing test", gantry_random_homing.run_gantry_random_homing_test),
    ("different direction test", gantry_diff_direction.run_gantry_diff_direction_test),
]

def confirm_paper_changed(next_test_name):
    while True:
        answer = input(
            f"Have you switched the paper for the {next_test_name}? (y/n): "
        ).strip().lower()

        if answer in ("y", "yes"):
            return

        print("Please switch the paper, then enter y when you are ready.")

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

        for test_number, (test_name, test_function) in enumerate(TESTS):
            print(f"\nStarting {test_name}...")
            test_function(ser, z_coor)
            print(f"{test_name} complete.")

            # The final test does not need another sheet of paper.
            if test_number < len(TESTS) - 1:
                next_test_name = TESTS[test_number + 1][0]
                confirm_paper_changed(next_test_name)

        print("\nAll gantry tests complete.")
    finally:
        ser.close()
        print("Serial connection closed.")

if __name__ == "__main__":
    main()
