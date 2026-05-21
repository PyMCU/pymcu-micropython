# DHT11 temperature and humidity driver (MicroPython style)
#
# Pass the DATA pin as a machine.Pin instance:
#   sensor = DHT11(Pin(2, Pin.IN))
#
# Call sensor.measure() to read; then check sensor.failed before using:
#   sensor.humidity     -- integer % RH (20-90)
#   sensor.temperature  -- integer degrees Celsius (0-50)
#   sensor.failed       -- True if the read failed or checksum mismatch
#
# Wiring:
#   DHT11 DATA -> pin passed in (e.g. D2), with 4.7 kohm pull-up to +5 V
#   DHT11 VCC  -> +5 V
#   DHT11 GND  -> GND
#
# Protocol (single-wire, 40-bit):
#   1. MCU pulls low >= 18 ms  (start signal)
#   2. MCU releases, sensor pulls low ~80 us then high ~80 us (ACK)
#   3. 40 bits: each bit starts with ~50 us LOW; HIGH duration decides value:
#      count > 35 loop iterations = 1, else = 0
#   4. Checksum = lower 8 bits of sum of the first 4 bytes

from pymcu.types import uint8, inline
from machine import Pin as _Pin, time_pulse_us
from pymcu.time import delay_ms, delay_us


class DHT11:
    @inline
    def __init__(self, pin: _Pin):
        self._pin        = pin
        self.failed      = False
        self.humidity    = 0
        self.temperature = 0

    @inline
    def measure(self):
        # Start signal: hold low >= 18 ms, then release to input
        self._pin.mode(_Pin.OUT)
        self._pin.low()
        delay_ms(18)
        self._pin.mode(_Pin.IN)
        delay_us(40)

        # ACK: sensor pulls low ~80 us, then high ~80 us
        if time_pulse_us(self._pin, 0, 200) < 0:
            self.failed = True
            return
        if time_pulse_us(self._pin, 1, 200) < 0:
            self.failed = True
            return

        # Read five bytes: hum_int, hum_dec, temp_int, temp_dec, checksum
        hum_int:  uint8 = self._read_byte()
        hum_dec:  uint8 = self._read_byte()
        temp_int: uint8 = self._read_byte()
        temp_dec: uint8 = self._read_byte()
        checksum: uint8 = self._read_byte()

        expected: uint8 = (hum_int + hum_dec + temp_int + temp_dec) & 0xFF
        if checksum != expected:
            self.failed = True
            return

        self.failed      = False
        self.humidity    = hum_int
        self.temperature = temp_int

    @inline
    def _read_byte(self) -> uint8:
        result: uint8 = 0
        bit: uint8 = 0
        while bit < 8:
            # Wait for ~50 us LOW (start of bit)
            if time_pulse_us(self._pin, 0, 200) < 0:
                return 0
            # Measure HIGH duration: >35 us = bit 1, else = bit 0
            high_dur = time_pulse_us(self._pin, 1, 200)
            if high_dur < 0:
                return 0
            result = result << 1
            if high_dur > 35:
                result = result | 1
            bit = bit + 1
        return result
