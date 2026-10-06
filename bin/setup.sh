#!/bin/bash
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

echo "Python stuff now"

# Then we try and download the relevant Python libaries
VENV_DIR=".venv"

# Check / Create Virtual Environment 
if [ -d "$VENV_DIR" ] && [ -f "$VENV_DIR/pyvenv.cfg" ]; then
    echo "✓ Virtual environment already exists."
else
    echo "Creating virtual environment..."
    python3 -m venv "$VENV_DIR"
fi

source "$VENV_DIR/bin/activate"

Check if we have a venv that is active 
if [ -z "$VIRTUAL_ENV" ]; then
    echo "ERROR: Virtual environment not active!"
    exit 1
fi
echo "Active venv: $VIRTUAL_ENV"

# Check & Install Libraries 
python -m pip install --no-cache-dir -U pip setuptools wheel

# OpenCV (headless for RPi - no GUI)
if pip show opencv-python &> /dev/null; then
    echo "opencv-python-headless already installed"
else
    echo "Installing opencv-python-headless..."
    pip install --no-cache-dir opencv-python-headless
fi

# Ultralytics
if pip show ultralytics &> /dev/null; then
    echo "ultralytics already installed"
else
    echo "Installing ultralytics..."
    pip install --no-cache-dir ultralytics
fi

# Pyserial (To import serial)
if pip show pyserial &> /dev/null; then
    echo "pyserial already installed"
else
    echo "Installing pyserial..."
    pip install --no-cache-dir pyserial
fi

# Verify 
python -c "import cv2; print(f'OpenCV installed and working version: {cv2.__version__}')"
python -c "import ultralytics; print(f'Ultralytics installed and working version: {ultralytics.__version__}')"