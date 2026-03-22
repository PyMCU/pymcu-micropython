# Blink -- MicroPython style on Arduino Uno
#
# Demonstrates:
#   machine.Pin  -- integer pin numbers (D13 = PB5 built-in LED)
#   utime        -- sleep_ms() with no hardware timer dependency
#
# MicroPython equivalent:
#   from machine import Pin
#   from utime import sleep_ms
#   led = Pin(13, Pin.OUT)
#   while True:
#       led.value(1)
#       sleep_ms(500)
#       led.value(0)
#       sleep_ms(500)
#
# No changes required -- identical API via whisnake-micropython.
#
# Wiring:
#   No external wiring -- uses built-in LED on D13
#
# Expected behaviour:
#   LED blinks at 1 Hz (500 ms on / 500 ms off) indefinitely

from machine import Pin
from utime import sleep_ms


def main():
    led = Pin(13, Pin.OUT)
    while True:
        led.value(1)
        sleep_ms(500)
        led.value(0)
        sleep_ms(500)
