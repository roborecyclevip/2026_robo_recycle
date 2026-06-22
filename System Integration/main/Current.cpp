#include "Current.h"
#include <Arduino.h>

const int sensorPin = A9;
const float mVperAmp = 100;
const float referenceVoltage = 5.0; 

double read_current_sensor() {
    float adcValue = analogRead(sensorPin);

    float voltage = (adcValue / 1023.0) * referenceVoltage;

    float currentAmps = (voltage - 2.5) / (mVperAmp / 1000.0);

    return currentAmps;    

    // SerialPrint(F("Raw ADC: "));
    // SerialPrint(adcValue);


    // SerialPrint(F("\tVoltage: "));
    // SerialPrint(voltage, 3);

    // SerialPrint(F(" V\tCurrent: "));
    // SerialPrint(currentAmps, 3);

    // SerialPrint(" A\n");

    // delay(500);
}
