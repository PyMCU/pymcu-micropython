# Blink -- MicroPython style on Arduino Uno
#
# Demonstrates:
#   machine.Pin  -- integer pin numbers (D13 = PB5 built-in LED)
#   utime        -- sleep_ms() with no hardware timer dependency
#
# Wiring:
#   No external wiring -- uses built-in LED on D13
#
# Expected behaviour:
#   LED toggles at 1 Hz (500 ms per half-period) indefinitely

from machine import Pin
from utime import sleep_ms


def main():
    led = Pin(13, Pin.OUT)
    while True:
        led.toggle()
        sleep_ms(500)
