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

from pymcu.types import uint8, uint16, uint32, int16, inline, const, ptr, Callable
from pymcu.hal.gpio import Pin as _Pin
from pymcu.hal.uart import UART as _UART
from pymcu.hal.adc import AnalogPin as _AnalogPin
from pymcu.hal.pwm import PWM as _PWM
from pymcu.hal.spi import SPI as _SPI
from pymcu.hal.i2c import I2C as _I2C
from pymcu.hal.timer import Timer as _Timer
from pymcu.hal.watchdog import Watchdog as _Watchdog
from pymcu.hal.power import (
    sleep_idle as _sleep_idle,
    sleep_power_save as _sleep_power_save,
    sleep_power_down as _sleep_power_down,
)
from pymcu.hal.irq import (
    enable_interrupts as _enable_interrupts,
    disable_interrupts as _disable_interrupts,
)
from pymcu.chips import __FREQ__

# ---------------------------------------------------------------------------
# Module-level constants (MicroPython machine module compatibility)
# ---------------------------------------------------------------------------

# Power / sleep mode identifiers
IDLE      = 0
SLEEP     = 1
DEEPSLEEP = 2

# Reset cause codes
PWRON_RESET     = 0
HARD_RESET      = 1
WDT_RESET       = 2
DEEPSLEEP_RESET = 3
SOFT_RESET      = 4

# Wake reason codes
PIN_WAKE  = 0
RTC_WAKE  = 1
WLAN_WAKE = 2


# ---------------------------------------------------------------------------
# Compile-time Arduino Uno pin number -> port string helper
# ---------------------------------------------------------------------------

@inline
def _arduino_pin_name(n: const[uint8]) -> str:
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
        case 14:
            return "PC0"
        case 15:
            return "PC1"
        case 16:
            return "PC2"
        case 17:
            return "PC3"
        case 18:
            return "PC4"
        case 19:
            return "PC5"
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
    def __init__(self, pin_id: const[uint8], mode: const[uint8] = 1):
        # pin_id: Arduino Uno integer (0-13 digital, 14-19 = A0-A5 analog).
        self._name = _arduino_pin_name(pin_id)
        self._pin = _Pin(self._name, mode)

    @inline
    def __init__(self, pin_id: const[uint8], mode: const[uint8], pull: const[uint8]):
        # Three-arg form: Pin(2, Pin.IN, Pin.PULL_UP).
        # pull: Pin.PULL_UP (1) enables the AVR internal pull-up resistor.
        self._name = _arduino_pin_name(pin_id)
        self._pin = _Pin(self._name, mode, pull)

    @inline
    def __init__(self, pin_id: const[str], mode: const[uint8] = 1):
        # Direct port-string form: Pin("PB5", Pin.OUT).
        self._name = pin_id
        self._pin = _Pin(self._name, mode)

    @inline
    def __init__(self, pin_id: const[str], mode: const[uint8], pull: const[uint8]):
        # String + pull: Pin("PD2", Pin.IN, Pin.PULL_UP).
        self._name = pin_id
        self._pin = _Pin(self._name, mode, pull)

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
    def init(self, mode: const[uint8] = 255, pull: const[uint8] = 255):
        # Re-initialise the pin (MicroPython standard).  Uses sentinel 255
        # for "unchanged" (== uint8 representation of -1 used by hal).
        self._pin.init(mode, pull)

    @inline
    def __call__(self, x: uint8 = 255) -> uint8:
        # Fast shortcut equivalent to Pin.value([x])  (MicroPython standard).
        return self.value(x)

    @inline
    def irq(self, handler: Callable = 0, trigger: uint8 = IRQ_FALLING):
        # Standard MicroPython API: handler(pin) receives this Pin instance.
        # The compiler synthesizes a parameterless ISR wrapper that inlines
        # handler with self's ZCA constants, so pin.value() etc. resolve
        # at compile time with zero runtime overhead.
        _set_irq_zca_arg(handler, self)
        self._pin.irq(trigger, handler)

    @inline
    def mode(self, m: uint8 = 255) -> uint8:
        if m == 255:
            return self._pin.mode()
        self._pin.mode(m)
        return m


# ---------------------------------------------------------------------------
# time_pulse_us: measure pulse duration (MicroPython machine.time_pulse_us)
# ---------------------------------------------------------------------------

@inline
def time_pulse_us(pin: Pin, pulse_level: uint8, timeout_us: uint16 = 1000) -> int16:
    # Accepts a machine.Pin instance (standard MicroPython API).
    # Delegates to the underlying hal.gpio.Pin.pulse_in directly, without
    # going through machine.Pin (pulse_in is not part of the MP Pin API).
    # Returns the pulse width in microseconds, or -1 on timeout.
    result: uint16 = pin._pin.pulse_in(pulse_level, timeout_us)
    if result == 0:
        return -1
    return result


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
    def write(self, data: const[str]):
        # Overload: write a compile-time string literal (e.g. uart.write("OK\n")).
        # Maps to write_str; equivalent to uart.write(b"OK\n") in standard MicroPython.
        self._hw.write_str(data)

    @inline
    def read(self) -> uint8:
        return self._hw.read()

    @inline
    def readline(self, buf: bytearray) -> uint8:
        # Matches closest MicroPython approximation: readline(buf) reads until '\n'
        # (or len(buf)-1 bytes) into buf. len(buf) inferred at compile time.
        # Returns byte count stored (excludes newline).
        # Deviation: MicroPython readline() takes no args and returns bytes.
        # PyMCU uses a caller-provided buffer to avoid GC overhead.
        return self._hw.read_line(buf, len(buf))

    @inline
    def readline(self, buf: bytearray, max_len: uint8) -> uint8:
        # Two-arg form: explicit max_len cap (kept for backward compatibility).
        return self._hw.read_line(buf, max_len)

    @inline
    def readinto(self, buf: bytearray) -> uint8:
        # Matches MicroPython: readinto(buf) fills len(buf) bytes (blocking).
        # len(buf) folds to a compile-time constant from the array declaration.
        i: uint8 = 0
        n: uint8 = len(buf)
        while i < n:
            buf[i] = self._hw.read()
            i = i + 1
        return n

    @inline
    def any(self) -> uint8:
        # Returns 1 if at least one byte is waiting in the receive buffer (RXC0).
        # Standard MicroPython: uart.any() -> number of bytes available.
        return self._hw.available()

    @inline
    def write_str(self, s: const[str]):
        # PyMCU extension -- prefer write(str) for portability.
        self._hw.write_str(s)

    @inline
    def println(self, s: const[str]):
        # PyMCU extension -- prefer write(str) + write(10) for portability.
        self._hw.println(s)

    @inline
    def print_byte(self, value: uint8):
        # PyMCU extension -- prefer uart_write_decimal_u8 directly for portability.
        self._hw.print_byte(value)


# ---------------------------------------------------------------------------
# ADC
# ---------------------------------------------------------------------------

class ADC:
    @inline
    def __init__(self, pin: Pin):
        # pin: machine.Pin instance. Use Pin(14)-Pin(19) for A0-A5 on Arduino Uno.
        # Extracts the CT port string (e.g. "PC0") from pin._name for the HAL.
        self._adc = _AnalogPin(pin._name)

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
    def __init__(self, pin: Pin, freq: uint16 = 1000, duty_u16: uint16 = 0):
        # pin: machine.Pin instance on a PWM-capable GPIO (D3/D5/D6/D9/D10/D11 on Uno).
        # Extracts the CT port string from pin._name for the HAL.
        duty8: uint8 = duty_u16 >> 8
        self._pwm = _PWM(pin._name, duty8, freq)

    @inline
    def freq(self, value: uint16):
        self._pwm.set_freq(value)

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
    def write(self, buf: bytearray):
        # Matches MicroPython: write(buf) transmits len(buf) bytes.
        # len(buf) folds to a compile-time constant from the array's declaration.
        self._spi.write_bytes(buf, len(buf))

    @inline
    def read(self, write_byte: uint8 = 0xFF) -> uint8:
        return self._spi.transfer(write_byte)

    @inline
    def readinto(self, buf: bytearray):
        # Matches MicroPython: readinto(buf) fills len(buf) bytes; sends 0xFF dummy.
        self._spi.readinto_n(buf, len(buf), 0xFF)

    @inline
    def readinto(self, buf: bytearray, write_byte: uint8):
        # readinto(buf, write_byte) -- custom dummy byte on MOSI.
        self._spi.readinto_n(buf, len(buf), write_byte)

    @inline
    def write_readinto(self, out: uint8, in_val: uint8) -> uint8:
        return self._spi.transfer(out)

    @inline
    def write_readinto(self, write_buf: bytearray, read_buf: bytearray):
        # Matches MicroPython: write_readinto(write_buf, read_buf) infers len from write_buf.
        self._spi.write_readinto_n(write_buf, read_buf, len(write_buf))


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
        # Returns number of responding devices (not a list).
        # Deviation: MicroPython scan() returns a list of addresses.
        # Use scan(buf, max_count) to also capture the addresses.
        count: uint8 = 0
        addr: uint8 = 1
        while addr < 128:
            if self._i2c.ping(addr):
                count += 1
            addr += 1
        return count

    @inline
    def scan(self, buf: bytearray, max_count: uint8) -> uint8:
        # Scans addresses 0x01-0x7F; stores each responding address in buf.
        # Returns the number of devices found (up to max_count).
        # Deviation: MicroPython scan() returns a list; PyMCU uses caller-owned buffer.
        count: uint8 = 0
        addr: uint8 = 1
        while addr < 128:
            if self._i2c.ping(addr):
                if count < max_count:
                    buf[count] = addr
                    count = count + 1
            addr = addr + 1
        return count

    @inline
    def writeto(self, addr: uint8, data: uint8):
        self._i2c.start()
        self._i2c.write(addr << 1)
        self._i2c.write(data)
        self._i2c.stop()

    @inline
    def writeto(self, addr: uint8, buf: bytearray):
        # Matches MicroPython: writeto(addr, buf) sends len(buf) bytes.
        self._i2c.write_bytes(addr, buf, len(buf))

    @inline
    def readfrom(self, addr: uint8) -> uint8:
        self._i2c.start()
        self._i2c.write((addr << 1) | 1)
        val: uint8 = self._i2c.read_nack()
        self._i2c.stop()
        return val

    @inline
    def readfrom_into(self, addr: uint8, buf: bytearray) -> uint8:
        # Matches MicroPython: readfrom_into(addr, buf) fills len(buf) bytes.
        # Returns 1 on success, 0 on NACK (MicroPython returns None; PyMCU reports status).
        return self._i2c.read_n(addr, buf, len(buf))


# ---------------------------------------------------------------------------
# freq: CPU clock frequency
# ---------------------------------------------------------------------------

@inline
def freq() -> uint32:
    # Returns the CPU clock frequency in Hz (compile-time constant from pyproject.toml).
    return __FREQ__


# ---------------------------------------------------------------------------
# IRQ control
# ---------------------------------------------------------------------------

@inline
def disable_irq() -> uint8:
    # Disable global interrupts. Returns 1 so that enable_irq(state) can
    # unconditionally re-enable on restore (MicroPython convention).
    _disable_interrupts()
    return 1


@inline
def enable_irq(state: uint8 = 1):
    # Re-enable global interrupts. state is the value returned by disable_irq().
    # Any non-zero state re-enables; zero leaves interrupts disabled.
    if state != 0:
        _enable_interrupts()


# ---------------------------------------------------------------------------
# Power / sleep
# ---------------------------------------------------------------------------

@inline
def reset():
    # Soft reset: jump to address 0 to re-run the startup stub.
    asm("jmp 0")


@inline
def idle():
    # Enter idle sleep (CPU halted, peripherals running). Wakes on any interrupt.
    _sleep_idle()


@inline
def lightsleep():
    # Enter light sleep (power-save mode). Keeps async timer running.
    _sleep_power_save()


@inline
def deepsleep():
    # Enter deep sleep (power-down mode). Wakes on external interrupt or WDT.
    _sleep_power_down()


# ---------------------------------------------------------------------------
# Timer
# ---------------------------------------------------------------------------

class Timer:
    ONE_SHOT  = 0
    PERIODIC  = 1
    IRQ_OVF   = 1
    IRQ_COMPA = 2

    @inline
    def __init__(self, id: const[uint8] = 255, prescaler: uint16 = 64,
                 period: const[uint16] = 0, mode: const[uint8] = 1,
                 callback: Callable = 0, freq: const[uint32] = 0):
        # id: compile-time timer number (0, 1, 2 for AVR).
        # id=255 is a sentinel for MicroPython Timer(-1) "auto-pick";
        # maps to Timer1 (16-bit, best range for period=ms API).
        # If period != 0 or freq != 0, auto-configure CTC mode.
        # Use CT branching on id directly so _Timer() receives a CT constant,
        # keeping self._t._id as a CT string for timer dispatch in irq().
        if id == 255:
            self._t = _Timer(1, prescaler)
        else:
            self._t = _Timer(id, prescaler)
        if freq != 0:
            self.init(freq=freq, mode=mode, callback=callback)
        elif period != 0:
            self.init(period=period, mode=mode, callback=callback)

    @inline
    def init(self, period: const[uint16] = 0, mode: const[uint8] = 1,
             callback: Callable = 0, prescaler: uint16 = 0,
             freq: const[uint32] = 0):
        # MicroPython-compatible init().
        # period: desired interval in milliseconds (compile-time constant).
        # freq:   desired frequency in Hz (compile-time constant).
        #         Takes precedence over period when both are supplied.
        # mode:   Timer.ONE_SHOT (0) or Timer.PERIODIC (1, default).
        # callback: called on each tick.
        # prescaler: low-level override; ignored when period or freq is set.
        #
        # Prescaler selection for AVR Timer1 @ 16 MHz (16-bit, OCR fits uint16):
        #   freq >= 245 Hz: prescaler=1,    OCR = 16 000 000 / freq - 1
        #   freq >=  31 Hz: prescaler=8,    OCR =  2 000 000 / freq - 1
        #   freq >=   4 Hz: prescaler=64,   OCR =    250 000 / freq - 1
        #   freq >=   1 Hz: prescaler=1024, OCR =     15 625 / freq - 1
        #
        # Period-to-prescaler mapping:
        #   period <= 262 ms: prescaler=64,   OCR = 250 * period - 1  (exact)
        #   period <= 4194 ms: prescaler=1024, OCR = 15 * period       (~0.6 ms error/step)
        self._t.stop()
        if freq != 0:
            if freq >= 245:
                self._t.reinit(1)
                ocr: uint16 = uint16(16000000 // freq - 1)
            elif freq >= 31:
                self._t.reinit(8)
                ocr: uint16 = uint16(2000000 // freq - 1)
            elif freq >= 4:
                self._t.reinit(64)
                ocr: uint16 = uint16(250000 // freq - 1)
            else:
                self._t.reinit(1024)
                ocr: uint16 = uint16(15625 // freq - 1)
            self._t.set_compare(ocr)
            if callback != 0:
                self._t.irq(callback, Timer.IRQ_COMPA)
            _enable_interrupts()
        elif period != 0:
            if period <= 262:
                self._t.reinit(64)
                ocr: uint16 = uint16(250 * period - 1)
            else:
                self._t.reinit(1024)
                ocr: uint16 = uint16(15 * period)
            self._t.set_compare(ocr)
            if callback != 0:
                self._t.irq(callback, Timer.IRQ_COMPA)
            _enable_interrupts()
        else:
            if prescaler != 0:
                self._t.reinit(prescaler)
            self._t.start()

    @inline
    def deinit(self):
        # Stop the timer and disconnect its clock source.
        self._t.stop()

    @inline
    def start(self):
        self._t.start()

    @inline
    def irq(self, handler: Callable, trigger: uint8 = 1):
        # Standard MicroPython API: handler(timer) receives this Timer instance.
        # The compiler synthesizes a parameterless ISR wrapper with self's ZCA
        # constants bound, so timer.start()/deinit() etc. resolve at compile time.
        # trigger: Timer.IRQ_OVF (1) overflow, Timer.IRQ_COMPA (2) compare-match.
        _set_irq_zca_arg(handler, self)
        self._t.irq(handler, trigger)


# ---------------------------------------------------------------------------
# WDT (Watchdog Timer)
# ---------------------------------------------------------------------------

class WDT:
    @inline
    def __init__(self, id: uint8 = 0, timeout: uint16 = 5000):
        # timeout is in milliseconds (MicroPython convention).
        # id is accepted for API compatibility and ignored (single WDT on AVR).
        self._wdt = _Watchdog(timeout)
        self._wdt.enable()

    @inline
    def feed(self):
        # Reset the watchdog counter. Must be called within the timeout period.
        self._wdt.feed()


# ---------------------------------------------------------------------------
# Signal: active-high / active-low pin abstraction
# ---------------------------------------------------------------------------

class Signal:
    @inline
    def __init__(self, pin: Pin, invert: const[uint8] = 0):
        # pin:    machine.Pin instance (must already be configured as OUT or IN).
        # invert: 0 = active-high (default), 1 = active-low.
        self._pin = pin
        self._inv = invert

    @inline
    def on(self):
        # Drive pin to the active state.
        if self._inv:
            self._pin.low()
        else:
            self._pin.high()

    @inline
    def off(self):
        # Drive pin to the inactive state.
        if self._inv:
            self._pin.high()
        else:
            self._pin.low()

    @inline
    def value(self, x: uint8 = 255) -> uint8:
        # Read or write the logical (active) value.
        # value()  -> read: returns 1 if signal is active, 0 if inactive.
        # value(v) -> write: drives pin to produce the requested logical level.
        if x == 255:
            raw: uint8 = self._pin.value()
            if self._inv:
                return 1 - raw
            return raw
        if self._inv:
            self._pin.value(1 - x)
        else:
            self._pin.value(x)
        return x


# ---------------------------------------------------------------------------
# mem8 / mem16: raw memory access (MicroPython machine.mem8 / machine.mem16)
# ---------------------------------------------------------------------------

class _Mem8:
    @inline
    def __getitem__(self, addr: uint16) -> uint8:
        p: ptr[uint8] = ptr(addr)
        return p.value

    @inline
    def __setitem__(self, addr: uint16, value: uint8):
        p: ptr[uint8] = ptr(addr)
        p.value = value


class _Mem16:
    @inline
    def __getitem__(self, addr: uint16) -> uint16:
        p: ptr[uint16] = ptr(addr)
        return p.value

    @inline
    def __setitem__(self, addr: uint16, value: uint16):
        p: ptr[uint16] = ptr(addr)
        p.value = value


mem8  = _Mem8()
mem16 = _Mem16()


