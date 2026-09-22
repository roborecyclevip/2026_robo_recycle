#!/bin/python3
# 
# Unscrew routine for Raspeberry Pi for VIP Project RoboRecycle
# unscrew.py
# 
# This is a python script that run the unscrew routine for the VIP Project RoboRecycle
# TODO: Write down the steps this routine follows
#
#
# Written by Shayyan Ali (z5482111) on 09/06/2026 18:55
# Last editted: 09/06/2026 20:00
#
# Usage: ./unscrew.py
# If you don't want errors for vscode code, install this extension:
# vscode-arduino.vscode-arduino-community

# Z=88 means contact

import serial
import time
import csv

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

# We treat the index as some id num for each screw
coordinates_to_unscrew = []

# Get the coordinates from the CSV
with open('coordinates.csv', 'r') as file:
    for row in csv.reader(file):
        row = (float(row[0]), float(row[1]))
        coordinates_to_unscrew.push(row)

print(coordinates_to_unscrew)
# Output: [(10.0, 20.0), (113.0, 69.0), ...]   

for x, y in coordinates_to_unscrew:
    unscrew(x, y)
    time.sleep(1)

print("All screws done.")
