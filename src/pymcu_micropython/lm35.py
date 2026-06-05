# LM35 precision temperature sensor driver (MicroPython style)
#
# API:
#   sensor = LM35(ADC(Pin(14)))   # A0 = Pin(14) on Arduino Uno
#   sensor.read()                 -- raw ADC count (0-1023)
#   sensor.temperature()          -- degrees Celsius as float (e.g. 24.8)
#
# Conversion formula (5 V reference, 10-bit ADC):
#   V_out  = ADC_raw * 5000.0 / 1024  (mV)
#   Temp_C = V_out / 10.0             (LM35 outputs 10 mV/C)
#   => Temp_C = ADC_raw * 0.4882813
#
# Wiring (Arduino Uno / ATmega328P, 5 V supply):
#   LM35 VS   -> +5 V
#   LM35 GND  -> GND
#   LM35 VOUT -> A0 (or any analog input)
#
# Note: The LM35 does not require calibration.  For accurate results use
# the 5 V rail as the ADC reference (default on Arduino Uno).  With a 3.3 V
# supply replace the constant 500 with 330 and 5000 with 3300.

from pymcu.types import uint16, inline
from machine import ADC as _ADC


class LM35:
    @inline
    def __init__(self, adc: _ADC):
        # adc: machine.ADC instance (e.g. ADC(Pin(14)) for A0).
        self._adc = adc

    @inline
    def read(self) -> uint16:
        # Raw ADC count, 0-1023
        return self._adc.read()

    @inline
    def temperature(self):
        raw: uint16 = self._adc.read()
        return raw * 0.4882813
