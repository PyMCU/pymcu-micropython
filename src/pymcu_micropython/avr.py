# MicroPython-compatible avr module for PyMCU
#
# AVR-specific peripherals:
#   EEPROM  -- non-volatile byte storage (shim over pymcu.hal.eeprom)
#   SoftSPI -- bit-bang SPI (shim over pymcu.hal.softspi)
#   SoftI2C -- bit-bang I2C (shim over pymcu.hal.softi2c)
#
# All classes follow ZCA (zero-cost abstraction) rules:
#   - All methods are @inline
#   - No SRAM instance structs emitted beyond the wrapped HAL object
#
# Usage:
#   from avr import EEPROM, SoftSPI, SoftI2C
#   from machine import Pin
#
#   ee = EEPROM()
#   ee.write(0, 42)
#   val = ee.read(0)
#
#   scl = Pin(5, Pin.OUT)
#   sda = Pin(4, Pin.OUT)
#   i2c = SoftI2C(scl, sda)
#
#   sck  = Pin(13, Pin.OUT)
#   mosi = Pin(11, Pin.OUT)
#   miso = Pin(12, Pin.IN)
#   spi  = SoftSPI(sck, mosi, miso, baudrate=500)

from pymcu.types import uint8, uint16, uint32, inline
from pymcu.hal.eeprom import EEPROM as _EEPROM
from pymcu.hal.softspi import SoftSPI as _SoftSPI
from pymcu.hal.softi2c import SoftI2C as _SoftI2C


# ---------------------------------------------------------------------------
# EEPROM
# ---------------------------------------------------------------------------

class EEPROM:
    @inline
    def __init__(self):
        self._ee = _EEPROM()

    @inline
    def read(self, addr: uint16) -> uint8:
        return self._ee.read(addr)

    @inline
    def write(self, addr: uint16, value: uint8):
        self._ee.write(addr, value)


# ---------------------------------------------------------------------------
# SoftSPI
# ---------------------------------------------------------------------------

class SoftSPI:
    CONTROLLER = 0
    PERIPHERAL = 1

    @inline
    def __init__(self, sck, mosi, miso, baudrate: uint16 = 500, mode: uint8 = 0):
        # sck, mosi, miso: machine.Pin instances.
        # baudrate: target SCK frequency in kHz (controller mode only).
        # mode: SoftSPI.CONTROLLER (0) or SoftSPI.PERIPHERAL (1).
        self._spi = _SoftSPI(sck._pin, mosi._pin, miso._pin, mode, None, baudrate)

    @inline
    def transfer(self, data: uint8) -> uint8:
        return self._spi.transfer(data)

    @inline
    def write(self, data: uint8):
        self._spi.write(data)

    @inline
    def select(self):
        self._spi.select()

    @inline
    def deselect(self):
        self._spi.deselect()


# ---------------------------------------------------------------------------
# SoftI2C
# ---------------------------------------------------------------------------

class SoftI2C:
    @inline
    def __init__(self, scl, sda, freq: uint32 = 100000):
        # scl, sda: machine.Pin instances (must have external pull-ups).
        # freq: bus frequency in Hz; converted to half-period microseconds
        #   as half_us = 500_000 // freq (compile-time fold when freq is literal).
        #   100 kHz -> half_us=5, 400 kHz -> half_us=1.
        half_us: uint8 = 500000 // freq
        self._i2c = _SoftI2C(scl._pin, sda._pin, half_us)
        self._i2c.init()

    @inline
    def scan(self) -> uint8:
        # Returns count of responding devices (not a list -- no heap on MCU).
        count: uint8 = 0
        addr: uint8 = 1
        while addr < 128:
            if self._i2c.ping(addr):
                count = count + 1
            addr = addr + 1
        return count

    @inline
    def writeto(self, addr: uint8, data: uint8) -> uint8:
        return self._i2c.write_to(addr, data)

    @inline
    def readfrom(self, addr: uint8) -> uint8:
        return self._i2c.read_from(addr)

    @inline
    def ping(self, addr: uint8) -> uint8:
        return self._i2c.ping(addr)
