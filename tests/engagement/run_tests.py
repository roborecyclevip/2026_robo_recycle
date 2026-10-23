#!/usr/bin/env python3
"""Native simulations; no hardware movement. Requires g++ and MultiStepperLite."""
import os
from pathlib import Path
import subprocess
import tempfile

HERE = Path(__file__).resolve().parent
FIRMWARE = HERE.parents[1] / "System Integration/main"
LIBRARY = Path(os.environ.get(
    "MULTISTEPPERLITE_SRC", str(Path.home() / "Arduino/libraries/MultiStepperLite/src")
))

with tempfile.TemporaryDirectory(prefix="robo_engagement_tests_") as build:
    cases = {
        "detection": [HERE / "test_detection.cpp"],
        "flow": [HERE / "test_flow.cpp", FIRMWARE / "ScrewEngagement.cpp"],
        "hardware_helpers": [HERE / "test_hardware_helpers.cpp",
                             FIRMWARE / "Encoder.cpp", FIRMWARE / "STEPPERmotor.cpp",
                             LIBRARY / "MultiStepperLite.cpp"],
    }
    for name, sources in cases.items():
        executable = str(Path(build) / name)
        subprocess.run([
            "g++", "-std=c++11", "-Wall", "-Wextra", "-DARDUINO", "-DARDUINO_ARCH_AVR",
            "-I", str(HERE / "stubs"), "-I", str(FIRMWARE), "-I", str(LIBRARY),
            *map(str, sources), "-o", executable,
        ], check=True)
        subprocess.run([executable], check=True)
