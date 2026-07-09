#!/usr/bin/env python3

import serial
import time


PORT = "/dev/ttyACM0"
BAUDRATE = 115200
TIMEOUT = 1
RESET_DELAY_S = 2
MIN_X_MM = 0
MAX_X_MM = 250
MIN_Y_MM = 0
MAX_Y_MM = 250
STEP_MM = 5
RAISED_Z_MM = 50
DRILL_Z_MM = 110
HOME_POSITION = (0, 0, 0)


def send_goto(ser, x, y, z):
    cmd = f"GOTO {x} {y} {z}\n"
    ser.write(cmd.encode())
    print("Sent:", cmd.strip())

    while True:
        line = ser.readline().decode(errors="replace").strip()
        if line:
            print("Arduino:", line)

        if "Move complete." in line:
            return


def grid_coordinates():
    x_values = list(range(MIN_X_MM, MAX_X_MM + 1, STEP_MM))
    y_values = list(range(MIN_Y_MM, MAX_Y_MM + 1, STEP_MM))

    for row_index, y in enumerate(y_values):
        row_x_values = x_values if row_index % 2 == 0 else reversed(x_values)
        for x in row_x_values:
            yield x, y


def run_grid_test(ser):
    total_points = (
        ((MAX_X_MM - MIN_X_MM) // STEP_MM + 1)
        * ((MAX_Y_MM - MIN_Y_MM) // STEP_MM + 1)
    )

    print(
        f"Testing {total_points} coordinates from "
        f"({MIN_X_MM}, {MIN_Y_MM}) to ({MAX_X_MM}, {MAX_Y_MM}) "
        f"in {STEP_MM} mm steps."
    )

    send_goto(ser, *HOME_POSITION)

    for index, (x, y) in enumerate(grid_coordinates(), start=1):
        print(f"Point {index}/{total_points}: X={x}, Y={y}")
        send_goto(ser, x, y, RAISED_Z_MM)
        send_goto(ser, x, y, DRILL_Z_MM)
        send_goto(ser, x, y, RAISED_Z_MM)

    send_goto(ser, *HOME_POSITION)


def main():
    ser = serial.Serial(PORT, BAUDRATE, timeout=TIMEOUT)
    time.sleep(RESET_DELAY_S)

    run_grid_test(ser)

    print("Test sequence complete.")


if __name__ == "__main__":
    main()
