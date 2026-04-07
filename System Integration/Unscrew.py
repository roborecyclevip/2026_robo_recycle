import serial
import time

# Adjust your port (Raspberry Pi USB typically /dev/ttyACM0 or /dev/ttyUSB0)
ser = serial.Serial('/dev/ttyACM0', 115200, timeout=1)
time.sleep(2)  # give Arduino time to reset

def unscrew(x, y):
    cmd = f"UNSCREW {x} {y}\n"
    ser.write(cmd.encode())
    print("Sent:", cmd.strip())

    # Read Arduino output until UNSCREW finished
    while True:
        line = ser.readline().decode().strip()
        if line:
            print("Arduino:", line)
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
