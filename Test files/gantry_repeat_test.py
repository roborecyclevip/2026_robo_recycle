#!/usr/bin/env python3

import serial
import time


PORT = "/dev/ttyACM0"
BAUDRATE = 115200
TIMEOUT = 1
RESET_DELAY_S = 2


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


def cycle_move(ser, target, repeats):
    for i in range(repeats):
        print(f"Cycle {i + 1}/{repeats} to {target}")
        send_goto(ser, 0, 0, 0)
        send_goto(ser, *target)


def main():
    ser = serial.Serial(PORT, BAUDRATE, timeout=TIMEOUT)
    time.sleep(RESET_DELAY_S)

    cycle_move(ser, (0, 0, 115), 30)
    send_goto(ser, 0, 0, 0)
    send_goto(ser, 100, 100, 115)
    cycle_move(ser, (10, 10, 115), 30)
    send_goto(ser, 0, 0, 0)
    send_goto(ser, 250, 240, 115)

    print("Test sequence complete.")


if __name__ == "__main__":
    main()
