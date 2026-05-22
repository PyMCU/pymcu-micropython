# LM35 precision temperature sensor driver (MicroPython style)
#
# API:
#   sensor = LM35(ADC("A0"))   # or LM35("A0") -- channel string also accepted
#   sensor.read()              -- raw ADC count (0-1023)
#   sensor.temperature()       -- integer degrees Celsius
#   sensor.temperature_tenths()-- tenths of degrees C  (248 = 24.8 C)
#
# Conversion formula (5 V reference, 10-bit ADC):
#   V_out  = ADC_raw * 5000 / 1024  (mV)
#   Temp_C = V_out / 10             (LM35 outputs 10 mV/C)
#   => Temp_C         = ADC_raw * 500  // 1024   (integer C)
#   => Temp_tenths_C  = ADC_raw * 5000 // 1024   (tenths of C)
#
# Wiring (Arduino Uno / ATmega328P, 5 V supply):
#   LM35 VS   -> +5 V
#   LM35 GND  -> GND
#   LM35 VOUT -> A0 (or any analog input)
#
# Note: The LM35 does not require calibration.  For accurate results use
# the 5 V rail as the ADC reference (default on Arduino Uno).  With a 3.3 V
# supply replace the constant 500 with 330 and 5000 with 3300.

from pymcu.types import uint16, uint32, inline
from machine import ADC as _ADC


class LM35:
    @inline
    def __init__(self, pin):
        self._adc = _ADC(pin)

    @inline
    def read(self) -> uint16:
        # Raw ADC count, 0-1023
        return self._adc.read()

    @inline
    def temperature(self) -> uint16:
        # Integer degrees Celsius (truncated)
        # Intermediate product fits in uint32: max 1023 * 500 = 511500
        raw: uint16 = self._adc.read()
        t: uint32 = uint32(raw) * 500
        return t // 1024

    @inline
    def temperature_tenths(self) -> uint16:
        # Tenths of degrees Celsius, e.g. 248 = 24.8 C
        # Intermediate product fits in uint32: max 1023 * 5000 = 5115000
        raw: uint16 = self._adc.read()
        t: uint32 = uint32(raw) * 5000
        return t // 1024
