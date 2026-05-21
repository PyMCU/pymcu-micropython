# mem8-test -- raw memory access via machine.mem8
#
# Demonstrates machine.mem8 by blinking the built-in LED (D13 / PB5)
# by writing directly to AVR I/O registers, bypassing Pin entirely.
#
# AVR ATmega328P register map:
#   0x24 = DDRB   (data direction, port B)
#   0x25 = PORTB  (output latch, port B)
#   PB5  = bit 5  (Arduino D13 / built-in LED)
#
# MicroPython equivalent on a port that supports machine.mem8:
#   from machine import mem8
#   mem8[0x24] = mem8[0x24] | 0x20   # DDRB |= (1<<5)
#   while True:
#       mem8[0x25] = mem8[0x25] | 0x20
#       ...
#
# Wiring:  none -- built-in LED
# Expected: LED blinks at 2 Hz indefinitely

from machine import mem8
from utime import sleep_ms

DDRB:  int = 0x24
PORTB: int = 0x25
PB5:   int = 0x20


def main():
    mem8[DDRB] = mem8[DDRB] | PB5
    while True:
        mem8[PORTB] = mem8[PORTB] | PB5
        sleep_ms(250)
        mem8[PORTB] = mem8[PORTB] & 0xDF
        sleep_ms(250)
