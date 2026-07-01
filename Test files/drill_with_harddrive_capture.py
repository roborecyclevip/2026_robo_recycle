#!/usr/bin/env python3

import csv
from pathlib import Path
import re
import statistics
import time

import serial

from serial_config import BAUD_RATE, SERIAL_PORT


BLOCKS = 5
RUNS_PER_BLOCK = 15
PAUSE_BETWEEN_BLOCKS_S = 15
TIMEOUT = 1
RESET_DELAY_S = 2
RUN_TIMEOUT_S = 30
COMMAND = "DRILL -10000 50"
OUTPUT_CSV = "with_harddrive.csv"
CURRENT_RE = re.compile(r"current sensor:\s*([-+]?\d*\.?\d+)", re.IGNORECASE)


def collect_run_currents(ser, run_number, total_runs):
    currents = []
    deadline = time.monotonic() + RUN_TIMEOUT_S

    ser.write(f"{COMMAND}\n".encode())
    print(f"Run {run_number}/{total_runs}: sent {COMMAND}")

    while True:
        if time.monotonic() > deadline:
            raise TimeoutError(
                f"Run {run_number} did not finish within {RUN_TIMEOUT_S} seconds."
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
        writer.writerow(["block", "run", "sample", "current_A"])

        for row in rows:
            writer.writerow(
                [row["block"], row["run"], row["sample"], f'{row["current_A"]:.3f}']
            )

        writer.writerow([])
        writer.writerow(["statistic", "current_A"])
        writer.writerow(["max", f"{max(all_currents):.3f}"])
        writer.writerow(["min", f"{min(all_currents):.3f}"])
        writer.writerow(["mean", f"{statistics.mean(all_currents):.3f}"])


def main():
    rows = []
    total_runs = BLOCKS * RUNS_PER_BLOCK
    output_path = Path(__file__).resolve().parent / OUTPUT_CSV

    with serial.Serial(SERIAL_PORT, BAUD_RATE, timeout=TIMEOUT) as ser:
        time.sleep(RESET_DELAY_S)
        ser.reset_input_buffer()

        run_number = 1
        for block_number in range(1, BLOCKS + 1):
            print(f"Starting block {block_number}/{BLOCKS}")

            for _ in range(RUNS_PER_BLOCK):
                currents = collect_run_currents(ser, run_number, total_runs)
                if not currents:
                    raise RuntimeError(
                        f"No current readings captured for run {run_number}."
                    )

                for sample_index, current in enumerate(currents, start=1):
                    rows.append(
                        {
                            "block": block_number,
                            "run": run_number,
                            "sample": sample_index,
                            "current_A": current,
                        }
                    )

                run_number += 1

            if block_number < BLOCKS:
                print(
                    f"Pausing for {PAUSE_BETWEEN_BLOCKS_S} seconds before next block..."
                )
                time.sleep(PAUSE_BETWEEN_BLOCKS_S)

    write_csv(rows, output_path)
    print(f"Saved {len(rows)} current samples to {output_path}")


if __name__ == "__main__":
    main()
