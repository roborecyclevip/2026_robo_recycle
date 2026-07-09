#!/usr/bin/env python3

import csv
from pathlib import Path
import re
import statistics
import time

import serial

from serial_config import BAUD_RATE, SERIAL_PORT


CYCLES = 6
PAUSE_BETWEEN_CYCLES_S = 3
TIMEOUT = 1
RESET_DELAY_S = 2
RUN_TIMEOUT_S = 30
COMMANDS = [
    ("reverse", "DRILL -100000 -50"),
    ("forward", "DRILL 100000 50"),
]
OUTPUT_CSV = "with_harddrive.csv"
CURRENT_RE = re.compile(r"current sensor:\s*([-+]?\d*\.?\d+)", re.IGNORECASE)


def collect_run_currents(ser, cycle_number, phase_name, command):
    currents = []
    deadline = time.monotonic() + RUN_TIMEOUT_S

    ser.write(f"{command}\n".encode())
    print(f"Cycle {cycle_number}/{CYCLES} {phase_name}: sent {command}")

    while True:
        if time.monotonic() > deadline:
            raise TimeoutError(
                f"Cycle {cycle_number} {phase_name} did not finish within {RUN_TIMEOUT_S} seconds."
            )

        line = ser.readline().decode(errors="replace").strip()
        if not line:
            continue

        print("Arduino:", line)

        match = CURRENT_RE.search(line)
        if match:
            currents.append(float(match.group(1)))

        if line == "Done." or line == "TIMEOUT!":
            return currents


def write_csv(rows, output_path):
    all_currents = [row["current_A"] for row in rows]

    with open(output_path, "w", newline="") as csvfile:
        writer = csv.writer(csvfile)
        writer.writerow(["with harddrive"])
        writer.writerow(["cycle", "phase", "sample", "current_A"])

        for row in rows:
            writer.writerow(
                [row["cycle"], row["phase"], row["sample"], f'{row["current_A"]:.3f}']
            )

        writer.writerow([])
        writer.writerow(["statistic", "current_A"])
        writer.writerow(["max", f"{max(all_currents):.3f}"])
        writer.writerow(["min", f"{min(all_currents):.3f}"])
        writer.writerow(["mean", f"{statistics.mean(all_currents):.3f}"])


def main():
    rows = []
    output_path = Path(__file__).resolve().parent / OUTPUT_CSV

    with serial.Serial(SERIAL_PORT, BAUD_RATE, timeout=TIMEOUT) as ser:
        time.sleep(RESET_DELAY_S)
        ser.reset_input_buffer()

        for cycle_number in range(1, CYCLES + 1):
            print(f"Starting cycle {cycle_number}/{CYCLES}")

            for phase_name, command in COMMANDS:
                currents = collect_run_currents(ser, cycle_number, phase_name, command)
                if not currents:
                    raise RuntimeError(
                        f"No current readings captured for cycle {cycle_number} {phase_name}."
                    )

                for sample_index, current in enumerate(currents, start=1):
                    rows.append(
                        {
                            "cycle": cycle_number,
                            "phase": phase_name,
                            "sample": sample_index,
                            "current_A": current,
                        }
                    )

            if cycle_number < CYCLES:
                print(
                    f"Pausing for {PAUSE_BETWEEN_CYCLES_S} seconds before next cycle..."
                )
                time.sleep(PAUSE_BETWEEN_CYCLES_S)

    write_csv(rows, output_path)
    print(f"Saved {len(rows)} current samples to {output_path}")


if __name__ == "__main__":
    main()
