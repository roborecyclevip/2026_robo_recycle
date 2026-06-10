#!/bin/python3

import serial
import time

# Adjust your port (Raspberry Pi USB typically /dev/ttyACM0 or /dev/ttyUSB0)
ser = serial.Serial('/dev/ttyACM0', 115200, timeout=1)
time.sleep(2)  # give Arduino time to reset

def send_answer(prompt, valid_answers):
    while True:
        answer = input(prompt).strip().upper()
        if answer in valid_answers:
            serial_answer = valid_answers[answer]
            ser.write((serial_answer + "\n").encode())
            print("Sent:", serial_answer)
            return
        print("Please enter one of:", ", ".join(valid_answers.keys()))

def unscrew(x, y):
    cmd = f"UNSCREW {x} {y}\n"
    ser.write(cmd.encode())
    print("Sent:", cmd.strip())

    # Read Arduino output until UNSCREW finished
    while True:
        line = ser.readline().decode().strip()
        if line:
            print("Arduino:", line)

            if "Type YES or NO:" in line or "Please type YES or NO:" in line:
                send_answer("YES/NO > ", {"YES": "YES", "Y": "YES", "NO": "NO", "N": "NO"})
            elif "Move UP or DOWN?" in line or "Please type UP or DOWN:" in line:
                send_answer("UP/DOWN > ", {"UP": "UP", "U": "UP", "DOWN": "DOWN", "D": "DOWN"})

        if "UNSCREW complete." in line or "UNSCREW failed." in line:
            break

# Example: list of screws
screw_positions = [
    (233.5, 195.0),
    (233.5, 182.5),
    (233.5, 169.5),
    (222, 195.0),
    (222, 182.5),
    (222, 169.5),
    (210.5, 195.0),
    (210.5, 182.5),
    (210.5, 169.5)
    
]

for x, y in screw_positions:
    unscrew(x, y)
    time.sleep(1)

print("All screws done.")
