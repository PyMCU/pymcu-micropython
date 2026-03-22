# UART Echo -- MicroPython style on Arduino Uno
#
# Demonstrates:
#   machine.UART -- read/write single bytes
#   machine.Pin  -- LED blinks on each received byte
#   utime        -- sleep_ms() for LED feedback
#
# Wiring:
#   LED:    built-in on D13 (no external wiring needed)
#   Serial: USB-to-serial adapter to TX (D1) / RX (D0) at 9600 baud
#
# Expected behaviour:
#   Startup: sends "ECHO\n"
#   Loop: echoes every received byte; LED blinks on each byte

from machine import Pin, UART
from utime import sleep_ms
from whisnake.types import uint8


def main():
    led  = Pin(13, Pin.OUT)
    uart = UART(0, 9600)

    uart.write(69)    # E
    uart.write(67)    # C
    uart.write(72)    # H
    uart.write(79)    # O
    uart.write(10)    # \n

    while True:
        b: uint8 = uart.read()
        led.value(1)
        uart.write(b)
        led.value(0)
