# mem8-test -- raw I/O register access via pymcu.chips
#
# Demonstrates direct AVR I/O register access by blinking the built-in
# LED (D13 / PB5) through DDRB and PORTB without using Pin.
#
# pymcu.chips.atmega328p exposes every hardware register as a typed
# ptr[uint8] module-level constant. The compiler maps reads/writes to
# the appropriate instruction (IN/OUT for I/O registers, LDS/STS for
# extended I/O). No special compiler magic required -- ptr is the
# standard PyMCU mechanism for raw memory access.
#
# Wiring:  none -- built-in LED
# Expected: LED blinks at 2 Hz indefinitely

from pymcu.chips.atmega328p import DDRB, PORTB, PORTB5
from utime import sleep_ms

DDRB.value = DDRB.value | (1 << PORTB5)

while True:
    PORTB.value = PORTB.value | (1 << PORTB5)
    sleep_ms(250)
    PORTB.value = PORTB.value & ~(1 << PORTB5)
    sleep_ms(250)
