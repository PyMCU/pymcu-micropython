# ADC Read -- MicroPython style on Arduino Uno
#
# Demonstrates:
#   machine.ADC  -- read_u16() returns 0-65535 scaled from 10-bit ADC
#   machine.UART -- print values over serial
#   utime        -- sleep_ms() between readings
#
# Wiring:
#   A0: potentiometer center tap (or any analog voltage 0-5V)
#
# Expected behaviour:
#   Prints ADC value every 200 ms over UART at 9600 baud

from machine import UART, ADC
from utime import sleep_ms
from pymcu.types import uint16


def main():
    uart = UART(0, 9600)
    adc  = ADC("A0")

    uart.println("ADC ready")

    while True:
        val: uint16 = adc.read()    # 0-1023
        uart.write_str("ADC=")
        # Print high byte as proxy for value (0-255 range)
        from pymcu.types import uint8
        hi: uint8 = val >> 2        # scale 0-1023 to 0-255
        uart.print_byte(hi)
        sleep_ms(200)
