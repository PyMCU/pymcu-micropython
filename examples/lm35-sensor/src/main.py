# LM35 Temperature Sensor -- MicroPython style on Arduino Uno
#
# Demonstrates:
#   machine.ADC  -- analog read on A0
#   lm35.LM35    -- temperature conversion (integer and tenths)
#   utime        -- sleep_ms() between readings
#
# MicroPython equivalent (runs unmodified on any MicroPython board):
#   from machine import ADC
#   from utime import sleep_ms
#   from lm35 import LM35
#   sensor = LM35(ADC(0))
#
# Wiring:
#   LM35 VS   -> +5 V
#   LM35 GND  -> GND
#   LM35 VOUT -> A0
#
# UART output (115200 baud, auto-initialized by pymcu build):
#   Boot:   "LM35 ready"
#   Every 1 s:  "T: 24.8 C"   (integer part + tenths combined)

from machine import ADC, Pin
from utime import sleep_ms
from lm35 import LM35


sensor = LM35(ADC(Pin(14)))   # A0 = Pin(14) = PC0

print("LM35 ready")

while True:
    print("T: ", sensor.temperature(), " C", sep="")
    sleep_ms(1000)
