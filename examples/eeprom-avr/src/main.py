# eeprom-avr -- AVR EEPROM read / write
#
# Demonstrates avr.EEPROM to persist a counter across power cycles.
# On each boot the counter is read from EEPROM, incremented, written
# back, then the value is blinked out on the built-in LED (D13 / PB5):
#   - each digit blinked N times (1-second on / off per blink)
#   - 3-second pause between boots
#
# EEPROM address 0 holds the counter (0-9, wraps to 0 at 10).
#
# Wiring:  none -- built-in LED
# Expected: blink count increments by 1 each power cycle (wraps at 10)

from avr import EEPROM
from machine import Pin
from utime import sleep_ms

ADDR: int = 0


def main():
    led  = Pin(13, Pin.OUT)
    ee   = EEPROM()
    n: int = ee.read(ADDR)
    if n >= 10:
        n = 0
    count: int = n + 1
    ee.write(ADDR, count)
    i: int = 0
    while i < count:
        led.value(1)
        sleep_ms(500)
        led.value(0)
        sleep_ms(500)
        i = i + 1
    sleep_ms(3000)
