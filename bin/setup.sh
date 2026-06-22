#!/bin/dash
# 
# Setup script for Raspeberry Pi for VIP Project RoboRecycle
# setup.sh
# 
# This is a dash script that installs all the relevant arduino software for the 
# Raspberry Pi and any other dependencies needed for the VIP Project RoboRecycle
# Written by Shayyan Ali (z5482111) on 09/06/2026 18:55
# Last editted: 09/06/2026 20:00
#
# Usage: ./setup.sh
# If you don't want errors for vscode code, install this extension:
# vscode-arduino.vscode-arduino-community

CLI_VERSION="1.5.1"
AVR_CORE_VERSION="1.8.8"
HX711_LIB_VERSION="0.7.5"
MULTISTEPPERLITE_VERSION="1.2.0"
FQBN="arduino:avr:mega"
SKETCH_PATH="System Integration/main"
BUILD_PATH="/tmp/robo_recycle_build"
ARDUINO_PORT="${ARDUINO_PORT:-/dev/ttyACM0}"

# Check if we have the arduino cli, if not, we install it
if ! "$PWD"/bin/arduino-cli version
then
    rm -f "$PWD"/bin/arduino-cli # it's brocken anyway since it can't show version
    curl -fsSL https://raw.githubusercontent.com/arduino/arduino-cli/v"$CLI_VERSION"/install.sh | BINDIR="$PWD/bin" sh
fi

# Only uncomment below IF using load cell:
#########################
# Check for HX711 Library
if ! ("$PWD"/bin/arduino-cli lib list | grep -q '^HX711 Arduino Library ')
then
    "$PWD"/bin/arduino-cli lib update-index
    "$PWD"/bin/arduino-cli lib uninstall "HX711" || true
    "$PWD"/bin/arduino-cli lib install "HX711 Arduino Library@$HX711_LIB_VERSION"
fi
#########################

# Check for Stepper library
if ! ("$PWD"/bin/arduino-cli lib list | grep -q '^Stepper')
then
    "$PWD"/bin/arduino-cli lib update-index
    "$PWD"/bin/arduino-cli lib install "Stepper"
fi

# Check for MultiStepperLite library
if ! "$PWD"/bin/arduino-cli lib list | grep -q '^MultiStepperLite '
then
    "$PWD"/bin/arduino-cli lib update-index
    "$PWD"/bin/arduino-cli lib install "MultiStepperLite@$MULTISTEPPERLITE_VERSION"
fi

# This actually runs it
"$PWD"/bin/arduino-cli core update-index
"$PWD"/bin/arduino-cli core install "arduino:avr@$AVR_CORE_VERSION"
"$PWD"/bin/arduino-cli compile --build-path "$BUILD_PATH" --fqbn "$FQBN" "$SKETCH_PATH"
"$PWD"/bin/arduino-cli upload --input-dir "$BUILD_PATH" --fqbn "$FQBN" --port "$ARDUINO_PORT"
