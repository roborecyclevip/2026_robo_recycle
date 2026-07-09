#!/usr/bin/env python3

import csv
from pathlib import Path
import re
import statistics
import time

import serial

from serial_config import BAUD_RATE, SERIAL_PORT


RUNS = 30
TIMEOUT = 1
RESET_DELAY_S = 2
COMMAND = "DRILL -10000 50"
OUTPUT_CSV = "free_spinning.csv"
RUN_TIMEOUT_S = 30
CURRENT_RE = re.compile(r"current sensor:\s*([-+]?\d*\.?\d+)", re.IGNORECASE)


def collect_run_currents(ser, run_number):
    currents = []
    deadline = time.monotonic() + RUN_TIMEOUT_S

    ser.write(f"{COMMAND}\n".encode())
    print(f"Run {run_number}/{RUNS}: sent {COMMAND}")

    while True:
        if time.monotonic() > deadline:
            raise TimeoutError(f"Run {run_number} did not finish within {RUN_TIMEOUT_S} seconds.")

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
        writer.writerow(["free spinning"])
        writer.writerow(["run", "sample", "current_A"])

        for row in rows:
            writer.writerow([row["run"], row["sample"], f'{row["current_A"]:.3f}'])

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

        for run_number in range(1, RUNS + 1):
            currents = collect_run_currents(ser, run_number)
            if not currents:
                raise RuntimeError(f"No current readings captured for run {run_number}.")

            for sample_index, current in enumerate(currents, start=1):
                rows.append(
                    {
                        "run": run_number,
                        "sample": sample_index,
                        "current_A": current,
                    }
                )

    write_csv(rows, output_path)
    print(f"Saved {len(rows)} current samples to {output_path}")


if __name__ == "__main__":
    main()
