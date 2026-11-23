#!/usr/bin/env python3
"""Run with python3 unscrew_v2_probe.py to check engagement with the Arduino probe."""

from unscrew_v2 import SAFE_Z, TARGET_Z, main
from unscrew_v2_helper import move_to, run_engagement_check


def prepare_probe_engagement(connection, x, y):
    """Probe at the aligned screw position and return True after operator confirmation."""
    # Measure free spin above the HDD. The Arduino brakes before it replies.
    move_to(connection, x, y, SAFE_Z)
    baseline = run_engagement_check(connection, "PROBE_BASELINE", "PROBE_BASELINE:")
    if baseline != "READY":
        raise RuntimeError(f"Free-spin check stopped: {baseline}. Inspect before continuing.")

    # Lower with the drill stopped, then probe with XYZ stationary. The mount's
    # compliance accommodates small differences in screw height.
    move_to(connection, x, y, TARGET_Z)
    result = run_engagement_check(connection, "PROBE_SCREW", "PROBE_RESULT:")
    if result != "POSSIBLE_ENGAGEMENT":
        raise RuntimeError(f"Screw check stopped: {result}. Inspect before continuing.")

    answer = input("Possible engagement. Type YES if the bit is seated and ready to unscrew: ")
    if answer.strip().upper() != "YES":
        raise RuntimeError("Operator did not confirm engagement. Inspect before continuing.")
    return True


if __name__ == "__main__":
    main(prepare_probe_engagement)
