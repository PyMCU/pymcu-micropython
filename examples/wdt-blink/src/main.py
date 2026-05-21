# wdt-blink -- watchdog timer blink
#
# Demonstrates machine.WDT to set up the hardware watchdog and blink
# the built-in LED (D13 / PB5) while feeding the watchdog every 500 ms.
#
# If the watchdog is not fed within the configured timeout (2000 ms),
# the microcontroller resets. Stopping at the REPL or hanging on an
# exception will cause a reset.
#
# Wiring:  none -- built-in LED
# Expected: LED blinks at 1 Hz indefinitely; MCU resets if feed() is missed

from machine import Pin, WDT
from utime import sleep_ms

led = Pin(13, Pin.OUT)
wdt = WDT(timeout=2000)
while True:
    led.value(1)
    sleep_ms(500)
    wdt.feed()
    led.value(0)
    sleep_ms(500)
    wdt.feed()
