# MicroPython-compatible machine module for PyMCU
#
# Provides Pin, UART, ADC, PWM, SPI, I2C as ZCA (zero-cost) classes that
# mirror the MicroPython machine API.
#
# Usage (MicroPython style):
#   from machine import Pin, UART, ADC
#
#   led = Pin(13, Pin.OUT)        # Arduino Uno D13 = PB5
#   uart = UART(0, 9600)          # USART0
#   adc = ADC(Pin("A0"))          # ADC channel 0
#
# Integer pin numbers map to Arduino Uno digital pin names at compile time.
# String pin names ("PB5", "PC0", etc.) are also accepted directly.
#
# ZCA contract:
#   All methods are @inline -- no stack frame, no SRAM instance struct.
#   Pin number -> string name resolution happens at compile time via match/case.

from pymcu.types import uint8, uint16, uint32, inline, const
from pymcu.hal.gpio import Pin as _Pin
from pymcu.hal.uart import UART as _UART
from pymcu.hal.adc import AnalogPin as _AnalogPin
from pymcu.hal.pwm import PWM as _PWM
from pymcu.hal.spi import SPI as _SPI
from pymcu.hal.i2c import I2C as _I2C


# ---------------------------------------------------------------------------
# Compile-time Arduino Uno pin number -> port string helper
# ---------------------------------------------------------------------------

@inline
def _arduino_pin_name(n: uint8) -> str:
    # Maps Arduino Uno integer pin number to PyMCU port string.
    # D0-D7 -> PORTD; D8-D13 -> PORTB.
    # String constants are resolved at compile time (match/case DCE).
    match n:
        case 0:
            return "PD0"
        case 1:
            return "PD1"
        case 2:
            return "PD2"
        case 3:
            return "PD3"
        case 4:
            return "PD4"
        case 5:
            return "PD5"
        case 6:
            return "PD6"
        case 7:
            return "PD7"
        case 8:
            return "PB0"
        case 9:
            return "PB1"
        case 10:
            return "PB2"
        case 11:
            return "PB3"
        case 12:
            return "PB4"
        case 13:
            return "PB5"
        case _:
            return "PB5"


# ---------------------------------------------------------------------------
# Pin
# ---------------------------------------------------------------------------

class Pin:
    # Mode constants (MicroPython style)
    IN      = 1
    OUT     = 0

    # Pull constants
    PULL_UP   = 1
    PULL_DOWN = 2

    # Trigger constants (for irq())
    IRQ_FALLING = 1
    IRQ_RISING  = 2

    @inline
    def __init__(self, pin_id: uint8, mode: uint8 = 1):
        # pin_id is an Arduino Uno integer pin number (0-13).
        # _arduino_pin_name converts it to a port string at compile time via DCE.
        # machine.Pin constants now match hal.gpio.Pin: OUT=0, IN=1.
        # Use explicit branches so the compiler sees constant HAL mode values.
        self._pin = _Pin(_arduino_pin_name(pin_id), mode)

    @inline
    def high(self):
        self._pin.high()

    @inline
    def low(self):
        self._pin.low()

    @inline
    def on(self):
        self._pin.high()

    @inline
    def off(self):
        self._pin.low()

    @inline
    def toggle(self):
        self._pin.toggle()

    @inline
    def value(self, x: uint8 = 255) -> uint8:
        # MicroPython: Pin.value() reads, Pin.value(1) writes.
        # Sentinel 255 means "read" (no real Optional on MCU).
        if x == 255:
            return self._pin.value()
        self._pin.value(x)
        return x

    @inline
    def irq(self, trigger: uint8 = IRQ_FALLING):
        self._pin.irq(trigger)

    @inline
    def mode(self, m: uint8 = 255) -> uint8:
        if m == 255:
            return self._pin.mode()
        self._pin.mode(mode)
        return m


# ---------------------------------------------------------------------------
# UART
# ---------------------------------------------------------------------------

class UART:
    @inline
    def __init__(self, id: uint8 = 0, baudrate: uint16 = 9600):
        # id accepted for API compatibility; ATmega328P has one USART (USART0).
        self._hw = _UART(baudrate)

    @inline
    def write(self, data: uint8):
        self._hw.write(data)

    @inline
    def read(self) -> uint8:
        return self._hw.read()

    @inline
    def write_str(self, s: const[str]):
        self._hw.write_str(s)

    @inline
    def println(self, s: const[str]):
        self._hw.println(s)

    @inline
    def print_byte(self, value: uint8):
        self._hw.print_byte(value)


# ---------------------------------------------------------------------------
# ADC
# ---------------------------------------------------------------------------

class ADC:
    @inline
    def __init__(self, pin):
        # pin may be a Pin instance or a channel name string ("A0", "A1", ...).
        self._adc = _AnalogPin(pin)

    @inline
    def read(self) -> uint16:
        # MicroPython-style 10-bit read (0-1023)
        self._adc.start()
        return self._raw_read()

    @inline
    def _raw_read(self) -> uint16:
        # Read ADCL/ADCH after conversion completes.
        # Caller is responsible for starting conversion via start().
        from pymcu.types import ptr
        ADCSRA: ptr[uint8] = ptr(0x7A)
        ADCL:   ptr[uint8] = ptr(0x78)
        ADCH:   ptr[uint8] = ptr(0x79)
        while ADCSRA[6]:
            pass
        lo: uint8 = ADCL.value
        hi: uint8 = ADCH.value
        result: uint16 = lo + hi * 256
        return result

    @inline
    def read_u16(self) -> uint16:
        # MicroPython-style 16-bit read (0-65535, scaled from 10-bit).
        raw: uint16 = self.read()
        return raw * 64    # scale 0-1023 to 0-65472 (approx 0-65535)


# ---------------------------------------------------------------------------
# PWM
# ---------------------------------------------------------------------------

class PWM:
    @inline
    def __init__(self, pin, freq: uint16 = 1000, duty_u16: uint16 = 0):
        duty8: uint8 = duty_u16 >> 8   # scale 16-bit to 8-bit
        self._pwm = _PWM(pin, duty8)

    @inline
    def duty_u16(self, value: uint16):
        duty8: uint8 = value >> 8
        self._pwm.set_duty(duty8)

    @inline
    def duty(self, value: uint8):
        self._pwm.set_duty(value)

    @inline
    def init(self):
        self._pwm.start()

    @inline
    def deinit(self):
        self._pwm.stop()


# ---------------------------------------------------------------------------
# SPI
# ---------------------------------------------------------------------------

class SPI:
    @inline
    def __init__(self):
        self._spi = _SPI()

    @inline
    def init(self):
        pass    # SPI initialized in __init__

    @inline
    def deinit(self):
        pass

    @inline
    def write(self, data: uint8):
        self._spi.write(data)

    @inline
    def read(self, write_byte: uint8 = 0xFF) -> uint8:
        return self._spi.transfer(write_byte)

    @inline
    def write_readinto(self, out: uint8, in_val: uint8) -> uint8:
        return self._spi.transfer(out)


# ---------------------------------------------------------------------------
# I2C
# ---------------------------------------------------------------------------

class I2C:
    @inline
    def __init__(self, scl=None, sda=None, freq: uint32 = 100000):
        # scl/sda accepted for API compatibility; hardware pins are fixed on
        # ATmega328P (PC5=SCL, PC4=SDA) and configured inside _I2C.__init__.
        self._i2c = _I2C()

    @inline
    def scan(self) -> uint8:
        # Simplified: returns number of responding devices (not a list -- no heap).
        # For a full scan, use pymcu.hal.i2c.I2C directly.
        count: uint8 = 0
        addr: uint8 = 1
        while addr < 128:
            if self._i2c.ping(addr):
                count += 1
            addr += 1
        return count

    @inline
    def writeto(self, addr: uint8, data: uint8):
        self._i2c.start()
        self._i2c.write(addr << 1)
        self._i2c.write(data)
        self._i2c.stop()

    @inline
    def readfrom(self, addr: uint8) -> uint8:
        self._i2c.start()
        self._i2c.write((addr << 1) | 1)
        val: uint8 = self._i2c.read_nack()
        self._i2c.stop()
        return val
