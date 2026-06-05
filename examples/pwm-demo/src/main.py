# PWM + Soft PWM -- MicroPython style on Arduino Uno
#
# Demonstrates hardware PWM (Timer0, automatic) alongside software PWM
# (bit-banged in the main loop).  Both LEDs fade in opposite directions so
# the difference in smoothness is visible.
#
# Hardware PWM:  D6  (PD6 = OC0A, Timer0 Fast PWM, ~490 Hz)
# Soft PWM:      D13 (PB5, built-in LED, 50 Hz via bit-bang)
#
# Wiring:
#   D6  -- LED + 220 ohm resistor to GND  (hardware PWM output)
#   D13 -- built-in LED, no wiring needed (soft PWM output)
#
# UART output (115200 baud, auto-initialised by pymcu build):
#   Boot: "PWM+SOFTPWM ready"
#
# Hardware PWM cycle:  ~2 s  (0 -> 250 -> 0 in steps of 5, each 20 ms)
# Soft PWM cycle:      ~0.8 s (100 -> 0 -> 100 in steps of 5, each 20 ms)

from machine import Pin, PWM
from pymcu.types import uint8
from utime import sleep_us

# Hardware PWM: D6 = PD6 = OC0A (Timer0 Fast PWM, ~490 Hz at 16 MHz)
hw = PWM(Pin(6))
hw.init()

# Soft PWM: D13 = PB5 (built-in LED, any digital output pin works)
sw_pin = Pin(13, Pin.OUT)

print("PWM+SOFTPWM ready")

hw_duty: uint8 = 0
sw_duty: uint8 = 100   # out of 100 steps (0 = off, 100 = full on)
hw_up:   uint8 = 1
sw_up:   uint8 = 0     # start fading down so both are in opposite phase

while True:
    # Update hardware PWM compare register (one write, Timer does the rest)
    hw.duty(hw_duty)

    # Soft PWM: one period = 100 steps x 200 us = 20 ms (50 Hz)
    count: uint8 = 0
    while count < 100:
        if count < sw_duty:
            sw_pin.high()
        else:
            sw_pin.low()
        sleep_us(200)
        count = count + 1
    sw_pin.low()   # ensure pin is low at end of period

    # --- advance hardware PWM duty (0 -> 250 -> 0, step 5) ---
    if hw_up:
        if hw_duty >= 250:
            hw_up = 0
        else:
            hw_duty = hw_duty + 5
    else:
        if hw_duty <= 5:
            hw_up = 1
        else:
            hw_duty = hw_duty - 5

    # --- advance soft PWM duty (100 -> 0 -> 100, step 5) ---
    if sw_up:
        if sw_duty >= 100:
            sw_up = 0
        else:
            sw_duty = sw_duty + 5
    else:
        if sw_duty == 0:
            sw_up = 1
        else:
            sw_duty = sw_duty - 5
