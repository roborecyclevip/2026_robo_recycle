import serial
import time

# Replace with your Arduino serial port and baud rate
SERIAL_PORT = '/dev/ttyACM0'
BAUD_RATE = 9600

try:
    ser = serial.Serial(SERIAL_PORT, BAUD_RATE, timeout=1)
    time.sleep(2)  # Wait for Arduino to reset after connection
except serial.SerialException:
    print(f"Could not open serial port {SERIAL_PORT}")
    exit(1)

def send_command(cmd):
    cmd_str = cmd + '\n'          # Add newline as Arduino expects
    ser.write(cmd_str.encode())   # Send bytes
    time.sleep(0.1)               # Wait for Arduino to process

    # Read any available response
    while ser.in_waiting:
        response = ser.readline().decode().strip()
        if response:
            print("Arduino:", response)

def main():
    print("Type commands to send to Arduino. Type 'exit' to quit.")
    while True:
        user_input = input("> ").strip()
        if user_input.lower() == 'exit':
            break
        send_command(user_input)

    ser.close()
    print("Serial connection closed.")

if __name__ == "__main__":
    main()
