import serial
import time

# === CONFIGURATION ===
SERIAL_PORT = '/dev/ttyACM0'  # Change this to your port (e.g., COM3 on Windows, /dev/ttyUSB0 on Linux)
BAUD_RATE = 9600

# === CONNECT TO ARDUINO ===
def connect():
    try:
        ser = serial.Serial(SERIAL_PORT, BAUD_RATE, timeout=2)
        time.sleep(2)  # Wait for Arduino to reset
        print("Connected to Arduino.")
        return ser
    except Exception as e:
        print("Error connecting to Arduino:", e)
        return None

# === SEND COMMAND TO ARDUINO ===
def send_command(ser, command):
    if ser:
        ser.write((command + '\n').encode())
        print(f"Sent: {command}")
        # Read response (optional)
        while ser.in_waiting:
            response = ser.readline().decode().strip()
            if response:
                print(f"Arduino: {response}")
        time.sleep(0.1)  # Small delay between commands

# === MAIN MENU ===
def main():
    ser = connect()
    if not ser:
        return

    print("\nCommands:")
    print("  HOMEX     → Home X axis")
    print("  HOMEY     → Home Y axis")
    print("  HOMEZ     → Home Z axis")
    print("  XYx,y     → Move to XY coordinates in mm (e.g., XY50,20)")
    print("  Zz        → Move to Z height in mm (e.g., Z10)")
    print("  EXIT      → Exit the program\n")

    while True:
        command = input("Enter command: ").strip().upper()
        if command == "EXIT":
            break
        send_command(ser, command)

    ser.close()
    print("Disconnected.")

if __name__ == "__main__":
    main()
