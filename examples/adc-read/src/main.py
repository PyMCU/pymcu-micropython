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

from machine import UART, ADC, Pin
from utime import sleep_ms
from pymcu.types import uint16


def main():
    uart = UART(0, 9600)
    adc  = ADC(Pin(14))   # Pin(14) = A0 = PC0

    uart.write("ADC ready\n")

    while True:
        val: uint16 = adc.read_u16()    # 0-65472 (10-bit count << 6)
        # Print high byte as proxy for value (0-255 range)
        from pymcu.types import uint8
        hi: uint8 = val >> 8        # scale 0-65472 to 0-255
        print("ADC=", hi)
        sleep_ms(200)
