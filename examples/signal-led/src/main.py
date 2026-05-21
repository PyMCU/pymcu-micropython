# signal-led -- Signal blink (active-high and active-low)
#
# Demonstrates machine.Signal to control the built-in LED (D13 / PB5).
#
# Signal wraps a Pin and adds logical on/off semantics:
#   invert=0 (default): on() drives HIGH, off() drives LOW (active-high)
#   invert=1:           on() drives LOW,  off() drives HIGH (active-low)
#
# This example uses the default active-high mode matching the Arduino
# Uno built-in LED (cathode to GND through resistor, anode to D13).
#
# Wiring:  none -- built-in LED
# Expected: LED blinks at 1 Hz indefinitely

from machine import Pin, Signal
from utime import sleep_ms

pin = Pin(13, Pin.OUT)
led = Signal(pin)
while True:
    led.on()
    sleep_ms(500)
    led.off()
    sleep_ms(500)
