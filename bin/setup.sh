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

# Check if we have the arduino cli, if not, we install it
if ! arduino-cli version
then
    curl -LO https://downloads.arduino.cc/arduino-cli/arduino-cli_1.5.1_Linux_64bit.tar.gz
    tar -xf arduino-cli_1.5.1_Linux_64bit.tar.gz
    sudo mv arduino-cli /usr/local/bin/
    rm arduino-cli_1.5.1_Linux_64bit.tar.gz LICENSE.txt
fi

# Only uncomment below IF using load cell:
#########################
# # Check for HX711 Library
# if ! (arduino-cli lib list | grep -q HX711)
# then
#     arduino-cli lib update-index
#     arduino-cli lib install "HX711"
# fi
#########################

# Check for Stepper library
if ! (arduino-cli lib list | grep -q '^Stepper')
then
    arduino-cli lib update-index
    arduino-cli lib install "Stepper"
fi

# Check for MultiStepperLite library
if ! arduino-cli lib list | grep -q '^MultiStepperLite '
then
    arduino-cli lib update-index
    arduino-cli lib install "MultiStepperLite"
fi

# This actually runs it
arduino-cli core update-index
arduino-cli core install arduino:avr
arduino-cli compile --fqbn arduino:avr:mega "System Integration/main"


