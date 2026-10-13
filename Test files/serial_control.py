#!/bin/python3
import serial
import time
import threading
import readline # This should help with the whole shell read
# See here: https://stackoverflow.com/questions/1706945/how-to-get-interactive-input-from-user-and-to-be-able-to-use-arrowkeys-while-ent
# Module entry incase stackoverflow dies: https://docs.python.org/3/library/readline.html#module-readline

from serial_config import BAUD_RATE, SERIAL_PORT

try:
    ser = serial.Serial(SERIAL_PORT, BAUD_RATE, timeout=1)
    time.sleep(2)  # Wait for Arduino to reset after connection
except serial.SerialException:
    print(f"Could not open serial port {SERIAL_PORT}")
    exit(1)

# The reader runs beside the keyboard prompt, so neither blocks the other.
keep_reading = True

def read_responses():
    """
    Continuously read and print replies in the background.
    Inputs: none; uses the shared serial connection and keep_reading flag.
    Output: None. Prints each Arduino line as it arrives.
    """
    while keep_reading:
        response = ser.readline().decode(errors='replace').strip()
        if response:
            print("Arduino:", response, flush=True)

def send_command(cmd):
    """
    Send a command; the background reader handles its replies.
    Inputs: cmd is the command text to send.
    Output: None.
    """
    cmd_str = cmd + '\n'          # Add newline as Arduino expects
    ser.write(cmd_str.encode())   # Send bytes

def main():
    """
    Read keyboard commands while Arduino replies print in the background.
    Inputs: none; commands come from keyboard input.
    Output: None. Stops the reader and closes serial when leaving.
    """
    global keep_reading
    reader = threading.Thread(target=read_responses, daemon=True)
    reader.start()

    print("Type commands to send to Arduino. Type 'exit' to quit.")
    try:
        while True:
            user_input = input("> ").strip()
            if user_input.lower() == 'exit':
                break
            send_command(user_input)
    finally:
        keep_reading = False
        reader.join()  # readline finishes within the one-second serial timeout
        ser.close()
        print("Serial connection closed.")

if __name__ == "__main__":
    main()
