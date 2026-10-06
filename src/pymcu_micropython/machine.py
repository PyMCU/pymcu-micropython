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
# Integer pin numbers are the target board's own numbering, resolved at compile
# time by the HAL for that chip -- 13 is PB5 on an Uno and PB7 on a Mega. Chips
# with no board numbering (the bare ATtinys, the ATmega32U4) refuse a number and
# ask for a port name. String pin names ("PB5", "PC0", ...) are always accepted.
#
# ZCA contract:
#   All methods are @inline -- no stack frame, no SRAM instance struct.
#   Pin number -> string name resolution happens at compile time via match/case.

from typing import Optional

from pymcu.types import uint8, uint16, uint32, int16, inline, const, ptr, Callable
from pymcu.chips import __CHIP__, __FREQ__
from pymcu.exceptions import CompileError as _CompileError
from pymcu.hal.gpio import Pin as _Pin
from pymcu.hal.softi2c import SoftI2C as _SoftI2C
from pymcu.hal.softspi import SoftSPI as _SoftSPI
from pymcu.hal.uart import UART as _UART
from pymcu.time import delay_us as _delay_us
if __CHIP__.arch == "avr":
    # Imported from the AVR package rather than the pymcu.hal.gpio facade on
    # purpose. Re-exporting the name through that facade needs a wrapper def,
    # and wrapping breaks the compile-time fold: measured on an Uno, the extra
    # @inline layer turned Pin(13) into SBI 0x0A,7 (PD7) instead of SBI 0x04,5
    # (PB5). A wrong pin, silently. Reaching one level in keeps the fold exact,
    # and this import already sits inside the AVR-only branch.
    from pymcu.hal.avr.gpio import board_pin_name as _board_pin_name
    from pymcu.hal.adc import AnalogPin as _AnalogPin
    from pymcu.hal.pwm import PWM as _PWM
    from pymcu.hal.spi import SPI as _SPI
    from pymcu.hal.i2c import I2C as _I2C
    from pymcu.hal.timer import Timer as _Timer
    from pymcu.hal.watchdog import Watchdog as _Watchdog
else:
    # The RP UART HAL has no timed read: readinto's first-byte wait polls the
    # RX flag against the free-running microsecond TIMER (no init needed there).
    from pymcu.time import micros as _micros
from pymcu.hal.power import (
    sleep_idle as _sleep_idle,
    sleep_power_save as _sleep_power_save,
    sleep_power_down as _sleep_power_down,
)
from pymcu.hal.irq import (
    enable_interrupts as _enable_interrupts,
    save_and_disable_interrupts as _save_and_disable_interrupts,
    restore_interrupts as _restore_interrupts,
)

# ---------------------------------------------------------------------------
# Module-level constants (MicroPython machine module compatibility)
# ---------------------------------------------------------------------------

# Reset cause codes -- the rp2 port's own values (measured on real firmware).
# Upstream rp2 exports exactly these two; HARD_RESET / SOFT_RESET /
# DEEPSLEEP_RESET and the PIN_WAKE / RTC_WAKE / WLAN_WAKE wake codes are
# esp32-port names and are deliberately absent here.
PWRON_RESET = 1
WDT_RESET   = 3


# ---------------------------------------------------------------------------
# Board pin number -> port string
# ---------------------------------------------------------------------------
#
# The numbering is NOT kept here. It lives in the AVR GPIO HAL, one table per
# chip, next to the select_port/select_bit arms that already had to know it.
# This module used to carry its own Arduino Uno table and apply it to every AVR,
# which silently produced PB5 on parts where 13 is not PB5 at all: D13 is PB7 on
# a Mega and PC7 on a Leonardo, and on an ATtiny85 PB5 is the RESET pin. The
# per-chip tables the HAL grew in "Pin(13) works on AVR" were unreachable
# because this function answered first.
#
# `_board_pin_name` is @inline and matches on a compile-time constant, so the
# call folds to a string literal before _Pin ever sees it: Pin(13, Pin.OUT) and
# Pin("PB5", Pin.OUT) still emit the same bytes on an Uno.

# ---------------------------------------------------------------------------
# Pin
# ---------------------------------------------------------------------------

# The mode values below are the real MicroPython rp2 ones -- IN=0, OUT=1 --
# not this HAL's own convention. Every PyMCU GPIO HAL (AVR, PIC, RISC-V and
# the RP2040's own) numbers the directions the Arduino way, IN=1/OUT=0, so the
# mode is translated at the HAL call with a ternary, which folds on a const
# argument (an @inline helper's return would not stay a compile-time constant,
# and the const[...] parameters on the HAL side require one). Answering the
# HAL's numbers here was a both-value-diff against the real firmware: `mode ==
# Pin.IN` code ported from a board would have compared against 1 and silently
# matched OUT.


class Pin:
    # Mode constants -- the rp2 port's own values (measured on real firmware).
    IN         = 0
    OUT        = 1
    OPEN_DRAIN = 2

    # Pull constants
    PULL_UP   = 1
    PULL_DOWN = 2

    # Trigger constants (for irq()) -- rp2 edge-trigger bitmask values.
    IRQ_FALLING = 4
    IRQ_RISING  = 8

    @inline
    def __init__(self, pin_id: const[uint8], mode: const[uint8] = -1):
        # upstream default mode=-1 is "leave unchanged"; a fresh pin's
        # unchanged state is an input, which is HAL IN=1. The const keeps
        # its -1 spelling, so the ternary matches it by name.
        if mode < -1 or mode > Pin.OPEN_DRAIN:
            raise _CompileError("machine.Pin: mode must be Pin.IN, Pin.OUT, or Pin.OPEN_DRAIN.")
        if __CHIP__.arch == "arm":
            # GP0-GP29: pin number IS the SIO bit index -- no port-string mapping.
            # OPEN_DRAIN is refused: the rp GPIO is push-pull only, and passing 2
            # through to the HAL's mode() silently configures an input.
            if mode == Pin.OPEN_DRAIN:
                raise _CompileError("machine.Pin: OPEN_DRAIN is not a mode this chip can drive -- its GPIO is push-pull only. Drive the pin low for 0 and switch it to Pin.IN for 1, with an external pull-up (the AVR HAL refuses this the same way).")
            self._pin = _Pin(pin_id, 1 if mode == Pin.IN or mode == -1 else 0)
        elif __CHIP__.arch == "avr":
            # AVR: board number -> port string, per chip (see the HAL).
            self._name = _board_pin_name(pin_id)
            self._pin = _Pin(self._name, 1 if mode == Pin.IN or mode == -1 else (0 if mode == Pin.OUT else mode))
        else:
            raise _CompileError("machine.Pin: integer pin numbers are Arduino/AVR and RP2040 only; this chip has no board pin map. Use the port name instead, e.g. Pin(\"RA4\", Pin.OUT).")

    @inline
    def __init__(self, pin_id: const[uint8], mode: const[uint8], pull: const):
        if mode < -1 or mode > Pin.OPEN_DRAIN:
            raise _CompileError("machine.Pin: mode must be Pin.IN, Pin.OUT, or Pin.OPEN_DRAIN.")
        if __CHIP__.arch == "arm":
            if mode == Pin.OPEN_DRAIN:
                raise _CompileError("machine.Pin: OPEN_DRAIN is not a mode this chip can drive -- its GPIO is push-pull only. Drive the pin low for 0 and switch it to Pin.IN for 1, with an external pull-up (the AVR HAL refuses this the same way).")
            # The rp GPIO constructor accepts pull but never programs it, so the
            # pull is applied through pull(), which does -- and pull=None is
            # upstream's "no pull" spelling, the HAL's 0.
            self._pin = _Pin(pin_id, 1 if mode == Pin.IN or mode == -1 else 0)
            if pull is None:
                self._pin.pull(0)
            elif pull != -1:
                self._pin.pull(pull)
        elif __CHIP__.arch == "avr":
            self._name = _board_pin_name(pin_id)
            self._pin = _Pin(self._name, 1 if mode == Pin.IN or mode == -1 else (0 if mode == Pin.OUT else mode), 0 if pull is None else pull)
        else:
            raise _CompileError("machine.Pin: integer pin numbers are Arduino/AVR and RP2040 only; this chip has no board pin map. Use the port name instead, e.g. Pin(\"RA4\", Pin.OUT).")

    @inline
    def __init__(self, pin_id: const[str], mode: const[uint8] = -1):
        # Direct port-string form: Pin("PB5", Pin.OUT). mode stays const[uint8]
        # here: the overload dispatcher only separates the str overloads from
        # the int ones when mode is typed uint8 -- const or const[int16] both
        # made Pin("PB5", Pin.OUT) dispatch into the integer arm and feed the
        # port name to _board_pin_name.
        if mode < -1 or mode > Pin.OPEN_DRAIN:
            raise _CompileError("machine.Pin: mode must be Pin.IN, Pin.OUT, or Pin.OPEN_DRAIN.")
        self._name = pin_id
        self._pin = _Pin(self._name, 1 if mode == Pin.IN or mode == -1 else (0 if mode == Pin.OUT else mode))

    @inline
    def __init__(self, pin_id: const[str], mode: const[uint8], pull: const):
        # String + pull: Pin("PD2", Pin.IN, Pin.PULL_UP). pull=None is
        # upstream's "no pull" spelling; the HAL spells that 0.
        if mode < -1 or mode > Pin.OPEN_DRAIN:
            raise _CompileError("machine.Pin: mode must be Pin.IN, Pin.OUT, or Pin.OPEN_DRAIN.")
        self._name = pin_id
        self._pin = _Pin(self._name, 1 if mode == Pin.IN or mode == -1 else (0 if mode == Pin.OUT else mode), 0 if pull is None else pull)

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
    def value(self) -> uint8:
        # MicroPython: Pin.value() reads, Pin.value(1) writes -- two real
        # overloads (get by arity, not a sentinel default): a sentinel here
        # collided with 255 itself, the largest value a uint8 holds, so
        # pin.value(255) silently read instead of driving the pin high the
        # way MicroPython's own bool(x) truthiness does for any nonzero x.
        return self._pin.value()

    @inline
    def value(self, x: uint8):
        # Upstream's pin.value(x) is machine_pin_call, which returns None --
        # the write form answers nothing, so a ported `v = pin.value(1)`
        # binds None on a board and must bind None here.
        self._pin.value(x)

    @inline
    def init(self, mode: const[uint8] = -1, pull: const = -1, *,
             value: const = None, drive: const = None, alt: const = None):
        # MicroPython: init(mode=-1, pull=-1, *, value=None, drive=None, alt=None). -1
        # means "leave unchanged" for mode/pull on both this layer and the HAL (an unsigned
        # uint8's own two's-complement -1, verified byte-identical to the old literal 255
        # spelling this replaces). The HAL's own init() already takes value/drive/alt with
        # a matching -1-is-unchanged convention (drive's is 0, alt's is -1), so only the
        # None-to-sentinel translation lives here. drive=/alt= select the RP2040's pin-mux
        # and drive-strength, which this chip's GPIO does not have (docs/limitations.md):
        # passing either raises, the same as pymcu.hal.avr.gpio.Pin.init() already does.
        #
        # Each leaf below calls the HAL with only mode/pull/value/drive/alt themselves or
        # a literal -1/0 sentinel -- never a variable reassigned from one of those two --
        # because `const` parameters stay compile-time constants only along a straight
        # binding, not through a branch that reassigns a fresh local from them.
        # mode goes through the same upstream->HAL value translation the
        # constructor performs; -1 ("leave unchanged") passes through.
        if mode < -1 or mode > Pin.OPEN_DRAIN:
            raise _CompileError("machine.Pin.init: mode must be Pin.IN, Pin.OUT, or Pin.OPEN_DRAIN.")
        if __CHIP__.arch == "arm":
            # The rp2040/rp2350 GPIO HAL has no init(); pull, mode and value are
            # separate methods there. -1 stays "leave unchanged": an absent
            # branch never calls the HAL.
            if drive is not None:
                raise _CompileError("machine.Pin.init: the rp2040/rp2350 GPIO HAL exposes no drive-strength knob, so drive= cannot reach the hardware.")
            if alt is not None:
                raise _CompileError("machine.Pin.init: the rp2040/rp2350 GPIO HAL exposes no alternate-function mux, so alt= cannot reach the hardware.")
            if mode == Pin.OPEN_DRAIN:
                raise _CompileError("machine.Pin.init: OPEN_DRAIN is not a mode this chip can drive -- the rp GPIO is push-pull only and mode(2) in the HAL only floats the driver. Drive the pin low for 0 and switch it to Pin.IN for 1, with an external pull-up.")
            # The output latch is written BEFORE the direction: init(OUT,
            # value=1) on a low-latched pin enabled the driver first and put a
            # low pulse on the wire. pull=None is upstream's "disable pulls"
            # spelling; the rp HAL spells that 0.
            if value is not None:
                self._pin.value(value)
            if pull is None:
                self._pin.pull(0)
            elif pull != -1:
                self._pin.pull(pull)
            if mode != -1:
                self._pin.mode(1 if mode == Pin.IN else 0)
        elif value is None:
            if drive is None:
                if alt is None:
                    self._pin.init(1 if mode == Pin.IN else (0 if mode == Pin.OUT else mode), 0 if pull is None else pull)
                else:
                    self._pin.init(1 if mode == Pin.IN else (0 if mode == Pin.OUT else mode), 0 if pull is None else pull, -1, 0, alt)
            else:
                if alt is None:
                    self._pin.init(1 if mode == Pin.IN else (0 if mode == Pin.OUT else mode), 0 if pull is None else pull, -1, drive)
                else:
                    self._pin.init(1 if mode == Pin.IN else (0 if mode == Pin.OUT else mode), 0 if pull is None else pull, -1, drive, alt)
        else:
            if drive is None:
                if alt is None:
                    self._pin.init(1 if mode == Pin.IN else (0 if mode == Pin.OUT else mode), 0 if pull is None else pull, value)
                else:
                    self._pin.init(1 if mode == Pin.IN else (0 if mode == Pin.OUT else mode), 0 if pull is None else pull, value, 0, alt)
            else:
                if alt is None:
                    self._pin.init(1 if mode == Pin.IN else (0 if mode == Pin.OUT else mode), 0 if pull is None else pull, value, drive)
                else:
                    self._pin.init(1 if mode == Pin.IN else (0 if mode == Pin.OUT else mode), 0 if pull is None else pull, value, drive, alt)

    @inline
    def __call__(self) -> uint8:
        # pin() reads -- upstream wires the Pin type's call slot to the same
        # machine_pin_call as value(), so the spellings are interchangeable.
        return self.value()

    @inline
    def __call__(self, x: uint8):
        # pin(x) writes and, like value(x) upstream, returns None.
        self._pin.value(x)

    @inline
    def irq(self, handler: Callable = 0, trigger: uint8 = 12, *,
            priority: const[uint8] = 1, wake: const = None, hard: const = False):
        # Standard MicroPython API: handler(pin) receives this Pin instance.
        # The compiler synthesizes a parameterless ISR wrapper that inlines
        # handler with self's ZCA constants, so pin.value() etc. resolve
        # at compile time with zero runtime overhead.
        # Upstream's trigger is the rp2 GPIO bitmask -- IRQ_FALLING=4,
        # IRQ_RISING=8, both edges = 12, low level = 1, high level = 2 --
        # while the AVR HAL numbers the triggers its ISC bits can raise
        # 1..4. Translate once here; a trigger the chip cannot raise refuses.
        # priority/wake/hard: upstream's keywords exist but this chip has one
        # interrupt level, no GPIO wake source and no soft-handler scheduler --
        # every handler runs in interrupt context (upstream's hard=True), so
        # only a non-default priority or wake= is refused.
        if priority != 1:
            raise _CompileError("machine.Pin.irq: this chip has a single interrupt level; only priority=1 exists.")
        if wake is not None:
            raise _CompileError("machine.Pin.irq: this chip has no GPIO wake source; wake= is RP2-sleep only.")
        if trigger == 2:
            raise _CompileError("machine.Pin.irq: IRQ_HIGH_LEVEL (2) is not a trigger this chip can raise.")
        if trigger != Pin.IRQ_FALLING and trigger != Pin.IRQ_RISING and trigger != 12 and trigger != 1:
            raise _CompileError("machine.Pin.irq: trigger must be Pin.IRQ_FALLING, Pin.IRQ_RISING, both edges (their |), or low level (1).")
        _set_irq_zca_arg(handler, self)
        self._pin.irq(1 if trigger == Pin.IRQ_FALLING else (2 if trigger == Pin.IRQ_RISING else (3 if trigger == 12 else 4)), handler)


# ---------------------------------------------------------------------------
# time_pulse_us: measure pulse duration (MicroPython machine.time_pulse_us)
# ---------------------------------------------------------------------------

@inline
def time_pulse_us(pin: Pin, pulse_level: uint8, timeout_us: uint32 = 1000000) -> int16:
    # MicroPython: time_pulse_us(pin, pulse_level, timeout_us=1000000) -- the
    # upstream default is one second, so the parameter must be 32-bit. The
    # HAL's cycle-counted primitive takes a 16-bit window, so a timeout past
    # this chip's measurable ceiling is clamped to it -- the pin still answers
    # -1 on timeout, which is all the API contract says.
    # Accepts a machine.Pin instance (standard MicroPython API).
    # Delegates to the underlying hal.gpio.Pin.pulse_in directly, without
    # going through machine.Pin (pulse_in is not part of the MP Pin API).
    result: uint16 = pin._pin.pulse_in(pulse_level, 65535 if timeout_us > 65535 else uint16(timeout_us))
    if result == 0:
        return -1
    return result


# ---------------------------------------------------------------------------
# UART
# ---------------------------------------------------------------------------

@inline
def _rp_uart_tx_id(pin) -> int16:
    # Upstream machine_uart.c's IS_VALID_TX/IS_VALID_PERIPH: TX pads sit at
    # (pin & 3) == 0 on the RP2040 and at every even pin on the RP2350, and the
    # UART id is bit 3 of pin + 4 in both. -1 means the pin is no TX pad.
    if __CHIP__.name == "rp2350":
        if pin < 0 or pin > 47 or pin & 1:
            return -1
    elif pin < 0 or pin > 29 or pin & 3:
        return -1
    return (pin + 4) >> 3 & 1


@inline
def _rp_uart_rx_id(pin) -> int16:
    # IS_VALID_RX: (pin & 3) == 1 on the RP2040, every odd pin on the RP2350.
    if __CHIP__.name == "rp2350":
        if pin < 0 or pin > 47 or (pin & 1) == 0:
            return -1
    elif pin < 0 or pin > 29 or (pin & 3) != 1:
        return -1
    return (pin + 4) >> 3 & 1


class UART:
    @inline
    def __init__(self, id: const[uint8] = 0, baudrate: const[uint32] = 9600,
                 bits: const[uint8] = 8, parity: const = None, stop: const[uint8] = 1, *,
                 tx: Pin = None, rx: Pin = None, timeout: const[uint16] = 0,
                 timeout_char: const[uint16] = 0):
        # MicroPython: UART(id, baudrate=9600, bits=8, parity=None, stop=1, *, tx, rx,
        # timeout=0, timeout_char=0, ...). Silently configuring UART0 for a
        # UART(1, ...) would leave the caller wiring the wrong pins and blaming
        # the hardware -- on RP the second UART exists in silicon but this HAL
        # does not drive it, so it is refused instead of aliased.
        if id != 0:
            if __CHIP__.arch == "arm":
                raise _CompileError("machine.UART: the RP chip has UART0 and UART1, but this HAL drives UART0 only -- id must be 0.")
            raise _CompileError("machine.UART: this chip has a single USART; id must be 0.")
        # Upstream's parity is None, or an int whose low bit picks odd (1) over even (0);
        # the HAL numbers them 0 none, 1 even, 2 odd. Unannotated so the value stays a
        # compile-time constant on its way to the HAL's const params.
        par_hw = 0 if parity is None else (2 if parity & 1 else 1)
        if __CHIP__.arch == "arm":
            # UART0's pads route per-pin through the HAL constructor; upstream's
            # default when tx/rx go unnamed is the peripheral's own pair (GP0/GP1
            # on UART0). A machine.Pin carries its pad number in _pin._pin, which
            # folds to a constant here. Each pad's role is checked against the
            # chip's mux table -- IS_VALID_TX/IS_VALID_RX in machine_uart.c --
            # so tx=Pin(1) cannot silently transmit on GP0 the way it used to.
            if tx is not None:
                if _rp_uart_tx_id(tx._pin._pin) != 0:
                    raise _CompileError("machine.UART: bad TX pin -- UART0's TX pads are GP0, GP12, GP16 and GP28 on an RP2040 (every even pin on an RP2350); the other half of the table belongs to UART1, which this HAL does not drive.")
            if rx is not None:
                if _rp_uart_rx_id(rx._pin._pin) != 0:
                    raise _CompileError("machine.UART: bad RX pin -- UART0's RX pads are GP1, GP13, GP17 and GP29 on an RP2040 (every odd pin on an RP2350); the other half of the table belongs to UART1, which this HAL does not drive.")
            self._hw = _UART(baudrate,
                             0 if tx is None else tx._pin._pin,
                             1 if rx is None else rx._pin._pin,
                             bits, par_hw, stop)
        else:
            if tx is not None:
                if tx._name != "PD1":
                    raise _CompileError("machine.UART: the USART pins are fixed on this chip; TX is PD1 (Pin(1) on an Uno).")
            if rx is not None:
                if rx._name != "PD0":
                    raise _CompileError("machine.UART: the USART pins are fixed on this chip; RX is PD0 (Pin(0) on an Uno).")
            self._hw = _UART(baudrate, bits=bits, parity=par_hw, stop=stop)
        # How long a read waits for its first byte and then between bytes, in ms. Upstream
        # raises timeout_char to at least a frame and a bit (13 bit times) at this rate.
        self._timeout = timeout
        self._timeout_char = timeout_char if timeout_char > 13000 // baudrate + 1 else 13000 // baudrate + 1
        # One frame on the wire, in microseconds: start bit, data, parity, stop.
        self._frame_us = (1 + bits + (0 if parity is None else 1) + stop) * 1000000 // baudrate

    @inline
    def init(self, baudrate: const = -1, bits: const = -1, parity: const = -1,
             stop: const = -1, *, tx: Pin = None, rx: Pin = None,
             timeout: const = -1, timeout_char: const = -1):
        # MicroPython: init(...) reprograms the running UART, and upstream's
        # defaults are -1/None sentinels meaning "leave unchanged". init() with
        # no arguments is the honest no-op that says the same thing -- the
        # stored configuration is runtime state and cannot be re-read as the
        # compile-time constants the HAL constructors fold from, so a partial
        # call cannot be honoured either: touch any frame field and ALL FOUR
        # (plus both pads on RP, whose HAL routes them) must be passed
        # explicitly. timeout and timeout_char are runtime fields, so they are
        # the one thing a partial call may set alone.
        if baudrate == -1 and bits == -1 and parity == -1 and stop == -1 and tx is None and rx is None:
            # Frame and pads untouched; only the read timeouts may change.
            if timeout != -1:
                self._timeout = timeout
            if timeout_char != -1:
                self._timeout_char = timeout_char
            return
        if baudrate == -1 or bits == -1 or parity == -1 or stop == -1:
            raise _CompileError("machine.UART.init: the fields not passed live in runtime storage and cannot be re-read as the constants the HAL needs -- pass baudrate, bits, parity and stop explicitly, or call init() bare to keep the whole configuration.")
        par_hw = 0 if parity is None else (2 if parity & 1 else 1)
        if __CHIP__.arch == "arm":
            # The rp UART HAL has no reinit; constructing it again re-programs
            # the peripheral and re-routes the pads, which is the same thing --
            # but pads are const there too, so both must be named. Each pad's
            # role is checked against the chip's mux table, as in the ctor.
            if tx is None or rx is None:
                raise _CompileError("machine.UART.init: reprogramming re-routes the pads, and the routed pads are runtime state that cannot be re-read as constants -- pass tx= and rx= explicitly, or call init() bare.")
            if _rp_uart_tx_id(tx._pin._pin) != 0:
                raise _CompileError("machine.UART.init: bad TX pin -- UART0's TX pads are GP0, GP12, GP16 and GP28 on an RP2040 (every even pin on an RP2350); the other half of the table belongs to UART1, which this HAL does not drive.")
            if _rp_uart_rx_id(rx._pin._pin) != 0:
                raise _CompileError("machine.UART.init: bad RX pin -- UART0's RX pads are GP1, GP13, GP17 and GP29 on an RP2040 (every odd pin on an RP2350); the other half of the table belongs to UART1, which this HAL does not drive.")
            self._hw = _UART(baudrate, tx._pin._pin, rx._pin._pin, bits, par_hw, stop)
        else:
            if tx is not None:
                if tx._name != "PD1":
                    raise _CompileError("machine.UART.init: the USART pins are fixed on this chip; TX is PD1 (Pin(1) on an Uno).")
            if rx is not None:
                if rx._name != "PD0":
                    raise _CompileError("machine.UART.init: the USART pins are fixed on this chip; RX is PD0 (Pin(0) on an Uno).")
            self._hw.reinit(baudrate, bits, par_hw, stop)
        if timeout != -1:
            self._timeout = timeout
        if timeout_char != -1:
            self._timeout_char = timeout_char
        self._frame_us = (1 + bits + (0 if par_hw == 0 else 1) + stop) * 1000000 // baudrate

    @inline
    def deinit(self):
        # MicroPython: deinit() turns the UART off.
        self._hw.deinit()

    @inline
    def flush(self):
        # MicroPython: flush() waits until every byte written has been sent. Once the data
        # register is empty the last byte is in the shift register, and one frame later it
        # has left the pin; waiting that frame out may wait one frame more than needed.
        while not self._hw.tx_empty():
            pass
        _delay_us(self._frame_us)

    @inline
    def txdone(self) -> uint8:
        # MicroPython: txdone() is True when the shift register is idle. The flag that
        # says so on this chip (TXC) stays set from any earlier frame unless every write
        # clears it first, which this UART does not, so an answer here could say "done"
        # while the last byte is still going out. flush() waits it out instead.
        raise _CompileError("machine.UART.txdone: this chip's transmit-complete flag is not cleared per write, so it cannot say whether the last byte has left the pin. Use uart.flush(), which waits until it has.")

    @inline
    def write(self, buf: uint8) -> uint8:
        # Single-byte write: upstream's write(buf) takes a buffer, and a uint8
        # is the honest one-byte shape on a heap-less target. Returns the count
        # written, as upstream's write does.
        self._hw.write(buf)
        return 1

    @inline
    def write(self, buf: const[str]) -> uint16:
        # Overload: write a compile-time string literal (e.g. uart.write("OK\n")).
        # Maps to write_str; equivalent to uart.write(b"OK\n") in standard MicroPython.
        self._hw.write_str(buf)
        return len(buf)

    @inline
    def write(self, buf: bytearray) -> uint16:
        # MicroPython: write(buf) sends every byte of buf and returns how many.
        i: uint16 = 0
        n: uint16 = len(buf)
        while i < n:
            self._hw.write(buf[i])
            i = i + 1
        return n

    @inline
    def read(self) -> uint8:
        if __CHIP__.arch == "avr":
            return self._hw.read()
        else:
            # Upstream's no-arg read() returns the bytes waiting now -- or None
            # -- a heap shape this target cannot hold, and the HAL's one-byte
            # read() blocks, which is not what a board does. The buffer form is
            # honest: n = uart.readinto(buf) is the count, or None on empty.
            raise _CompileError("machine.UART.read() upstream returns the bytes available now as a bytes object, or None -- a heap shape this target cannot hold. Read into a buffer instead: buf = bytearray(n); count = uart.readinto(buf).")

    @inline
    def read(self, nbytes: uint16) -> uint8:
        # MicroPython: read(nbytes) returns however many bytes arrived before the
        # timeout, as a fresh bytes object, or None. A buffer of a fixed size cannot carry
        # a length decided at run time, so this refuses and names the form that can.
        raise _CompileError("machine.UART.read(nbytes): upstream returns as many bytes as arrived before the timeout, a length a fixed-size buffer cannot carry. Read into a buffer instead: buf = bytearray(n); count = uart.readinto(buf, n).")

    @inline
    def readline(self) -> uint8:
        # MicroPython's no-arg readline() returns a fresh bytes object, which
        # needs a heap. Error with the working alternative instead of failing
        # with a confusing arity mismatch.
        raise _CompileError("machine.UART.readline: the no-arg form returns a heap-allocated bytes object, which this target does not have. Declare a buffer and use readline(buf): buf: bytearray = bytearray(32); n = uart.readline(buf).")

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
    def readinto(self, buf: bytearray) -> Optional[uint16]:
        # MicroPython: readinto(buf) reads at most len(buf) bytes.
        return self.readinto(buf, len(buf))

    @inline
    def readinto(self, buf: bytearray, nbytes: uint16) -> Optional[uint16]:
        # MicroPython: readinto(buf, nbytes) reads at most nbytes into buf, waiting up to
        # `timeout` ms for the first byte and `timeout_char` ms for each one after, and
        # returns how many arrived. It used to block until the count was reached, which
        # is not what a board does at the default timeout of 0. Upstream answers None
        # when nothing arrived; on ARM this answers None too, on AVR it answers 0,
        # which reads the same under `if n:`.
        count: uint16 = 0
        wait: uint16 = self._timeout
        while count < nbytes:
            if __CHIP__.arch == "avr":
                c: int16 = self._hw.read_timeout(wait)
                if c < 0:
                    return count
                buf[count] = uint8(c)
            else:
                # No timed read in the rp UART HAL: poll the RX-not-empty flag
                # against the free-running microsecond TIMER (wrap-safe diff).
                start_us: uint32 = _micros()
                while self._hw.available() == 0:
                    if _micros() - start_us >= uint32(wait) * 1000:
                        if count == 0:
                            return None
                        return count
                buf[count] = self._hw.read()
            count = count + 1
            wait = self._timeout_char
        return count

    @inline
    def any(self) -> uint8:
        # Standard MicroPython: uart.any() -> number of bytes available.
        if __CHIP__.arch == "avr":
            # Returns 1 if at least one byte is waiting in the receive buffer (RXC0).
            return self._hw.available()
        else:
            # The rp UART FIFO reports only empty-or-not -- no count -- so a
            # count answered here would be false (1 for two queued bytes).
            raise _CompileError("machine.UART.any() is a byte count and this chip's UART FIFO reports only empty-or-not -- it cannot count. Poll readinto() instead; it reports how many bytes it actually got.")

    # The rp2 firmware's UART has no irq(), write_str(), println() or
    # print_byte() -- the stub's irq is an esp32-port declaration, and the
    # rest were PyMCU conveniences. println("x") callers write
    # uart.write("x\n"): a str is a buffer under MicroPython, so the byte
    # stream is identical to upstream's write(b"x\n").


# ---------------------------------------------------------------------------
# ADC
# ---------------------------------------------------------------------------

@inline
def _adc_channel_port(channel: const[uint8]) -> str:
    # Maps an ADC channel number to the PyMCU port string (A0-A5 on Uno).
    match channel:
        case 0:
            return "PC0"
        case 1:
            return "PC1"
        case 2:
            return "PC2"
        case 3:
            return "PC3"
        case 4:
            return "PC4"
        case 5:
            return "PC5"
        case _:
            # Unreachable: ADC.__init__ refuses a channel above 5 before calling this.
            # The compiler decides "every path returns" from the match alone, and a match
            # with no `case _:` has a path that falls out of the bottom -- so ADC(0), with
            # the channel a compile-time constant, was refused inside this function.
            raise _CompileError("machine.ADC: this chip has ADC channels 0-5 (A0-A5); use ADC(0)..ADC(5) or ADC(Pin(14))..ADC(Pin(19)).")


class ADC:
    @inline
    def __init__(self, pin: Pin):
        # pin: machine.Pin instance. Use Pin(14)-Pin(19) for A0-A5 on Arduino Uno.
        # Extracts the CT port string (e.g. "PC0") from pin._name for the HAL.
        self._adc = _AnalogPin(pin._name)

    @inline
    def __init__(self, channel: const[uint8]):
        # ESP-style channel number (MicroPython quickref: machine.ADC(0)).
        # Channels 0-5 map to A0-A5 (PC0-PC5) on the Arduino Uno.
        if channel > 5:
            raise _CompileError("machine.ADC: this chip has ADC channels 0-5 (A0-A5); use ADC(0)..ADC(5) or ADC(Pin(14))..ADC(Pin(19)).")
        self._adc = _AnalogPin(_adc_channel_port(channel))

    @inline
    def __init__(self, pin_name: const[str]):
        # The port-string form, which is what the board modules spell A0..A5 as
        # (arduino_uno.A0 is "PC0"): ADC(arduino_uno.A0).
        self._adc = _AnalogPin(pin_name)

    @inline
    def __init__(self, other: "ADC"):
        # ADC(an_adc) is the identity. A driver that takes "an ADC or something an ADC can be
        # made from" calls ADC() on whatever it was given, and LM35(ADC(Pin("PC0"))) is that
        # shape: LM35.__init__ calls ADC(pin) again on a value that is already one.
        #
        # Without this overload the call selected __init__(self, pin: Pin) and read pin._name
        # on an ADC, which has no _name. That read used to be accepted inside a constructor and
        # lowered against a slot nothing writes, so the channel table became a run-time
        # comparison of a pin name against a byte of BSS and the refusal in its default arm
        # became a warning: a pin with no channel behind it read channel 0 (PyMCU#318).
        #
        # Taking the field through is what keeps the pin name a compile-time constant, so the
        # table folds to one LDI here exactly as it does without the wrapper.
        self._adc = other._adc

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
        # MicroPython-style 16-bit read (0-65535, scaled from 10-bit) -- the
        # only ADC read the rp2 port exposes; there is no 0..1023 read().
        self._adc.start()
        # Scaled the way the rp2 port scales its 12-bit reading, raw << (16 - bits) |
        # raw >> (2 * bits - 16): the top bits are copied into the bottom ones, so full
        # scale is 65535 and zero is 0. raw * 64 stopped at 65472. The two halves share no
        # bits, so + is the same |, and it is 8 bytes smaller here.
        raw: uint16 = self._raw_read()
        return raw * 64 + (raw >> 4)


# ---------------------------------------------------------------------------
# PWM
# ---------------------------------------------------------------------------

# duty_ns <-> duty_u16 at a frequency, in 32-bit integer arithmetic: the high time is
# ns * freq / 1e9 of a period, and a period is 65536 duty_u16 steps. With q = (ns / 10) *
# freq, which stays at or below 1e8 for any high time up to one period, the duty is
# q * 65536 / 1e8 = q * 40 / 61035.16: q * 40 fits 32 bits and the 1 / 61035 is exact to
# 3 parts per million, so 500 us at 1 kHz lands on 32768 as in MicroPython. A high time
# past the period saturates at 100 %.
@inline
def _duty_ns_to_u16(ns: uint32, freq: uint16) -> uint16:
    q: uint32 = (ns // 10) * freq
    if q > 100000000:
        return 65535
    scaled: uint32 = q * 40 // 61035
    if scaled > 65535:
        return 65535
    return scaled


@inline
def _duty_u16_to_ns(duty: uint16, freq: uint16) -> uint32:
    if freq == 0:
        return 0
    wide: uint32 = duty
    return wide * 15259 // freq


class PWM:
    @inline
    def __init__(self, pin: Pin, freq: uint16 = 1000, duty_u16: uint16 = 0,
                 duty_ns: uint32 = 0, invert: const[uint8] = 0):
        # pin: machine.Pin instance on a PWM-capable GPIO (D3/D5/D6/D9/D10/D11 on Uno).
        # Extracts the CT port string from pin._name for the HAL.
        # duty_ns, when given, wins over duty_u16 (MicroPython: the last one set applies;
        # a constructor takes one or the other). invert selects the inverting output.
        # The field is laid out from this first store: a uint16 parameter gives it sixteen
        # bits (an annotated local did not, and duty_u16(16384) then read back as 0).
        self._freq = freq
        self._duty = duty_u16
        if duty_ns != 0:
            self._duty = _duty_ns_to_u16(duty_ns, freq)
        self._pwm = _PWM(pin._name, freq=freq, invert=invert, duty_u16=self._duty)

    @inline
    def freq(self) -> uint16:
        # Getter (MicroPython: pwm.freq() with no args reads the frequency).
        # Returns the last requested value; the timer runs at the nearest
        # achievable prescaler bucket, which may differ.
        return self._freq

    @inline
    def freq(self, value: uint16):
        # MicroPython: freq(value) retunes the channel and keeps its duty_u16, so the duty
        # is set again against the new period. A Timer1 channel (D9/D10) takes any
        # frequency, including one that arrives at run time; the 8-bit timers' channels
        # run at the nearest of their prescaler buckets. Zero is upstream's ValueError.
        if value == 0:
            raise ValueError("freq too small")
        self._freq = value
        self._pwm.set_freq(value)
        self._pwm.set_duty_u16(self._duty)

    @inline
    def duty_u16(self) -> uint16:
        # Getter (MicroPython: pwm.duty_u16() with no args reads the duty).
        return self._duty

    @inline
    def duty_u16(self, value: uint16):
        self._duty = value
        self._pwm.set_duty_u16(value)

    @inline
    def duty_ns(self) -> uint32:
        # Getter: the high time in nanoseconds at the current frequency.
        return _duty_u16_to_ns(self._duty, self._freq)

    @inline
    def duty_ns(self, value: uint32):
        duty16: uint16 = _duty_ns_to_u16(value, self._freq)
        self._duty = duty16
        self._pwm.set_duty_u16(duty16)

    @inline
    def init(self, *, freq: uint16 = 0, duty_u16: uint16 = 0, duty_ns: uint32 = 0):
        # MicroPython: init(*, freq, duty_u16, duty_ns) -- keyword-only, so a
        # positional init(20000) refuses here exactly as it does on a board.
        # init() reprograms what is given and
        # (re)starts the output. A 0 here means "not given": duty_u16=0 alone does not
        # switch the output off, use duty_u16(0) for that.
        if freq != 0:
            self.freq(freq)
        if duty_u16 != 0:
            self.duty_u16(duty_u16)
        if duty_ns != 0:
            self.duty_ns(duty_ns)
        self._pwm.start()

    @inline
    def deinit(self):
        self._pwm.stop()


# ---------------------------------------------------------------------------
# SPI
# ---------------------------------------------------------------------------

@inline
def _spi_check_pins(sck: Pin, mosi: Pin, miso: Pin):
    # The hardware SPI's pins are fixed: naming them is accepted, any other is refused.
    if sck is not None:
        if sck._name != "PB5":
            raise _CompileError("machine.SPI: the SPI pins are fixed on this chip; SCK is PB5 (Pin(13) on an Uno). Use SoftSPI to pick your own pins.")
    if mosi is not None:
        if mosi._name != "PB3":
            raise _CompileError("machine.SPI: the SPI pins are fixed on this chip; MOSI is PB3 (Pin(11) on an Uno). Use SoftSPI to pick your own pins.")
    if miso is not None:
        if miso._name != "PB4":
            raise _CompileError("machine.SPI: the SPI pins are fixed on this chip; MISO is PB4 (Pin(12) on an Uno). Use SoftSPI to pick your own pins.")


class SPI:
    # Bit-order constants -- the rp2 port's own values, measured on real
    # firmware. The stub's CONTROLLER is declared but never defined on rp2
    # (the port's constructor has no role argument), so it is absent here.
    MSB = 1
    LSB = 0

    @inline
    def __init__(self, id: const[uint8] = 0, baudrate: const[uint32] = 1000000, *,
                 polarity: const[uint8] = 0, phase: const[uint8] = 0,
                 bits: const[uint8] = 8, firstbit: const[uint8] = 1,
                 sck: Pin = None, mosi: Pin = None, miso: Pin = None):
        # MicroPython: SPI(id, baudrate=1_000_000, polarity=0, phase=0, bits=8,
        # firstbit=SPI.MSB, sck=None, mosi=None, miso=None). This chip has a single SPI
        # bus with fixed hardware pins (SCK=PB5, MOSI=PB3, MISO=PB4), so sck=/mosi=/miso=
        # are accepted when they name those pins -- SPI(0, sck=Pin(13), mosi=Pin(11),
        # miso=Pin(12)) on an Uno -- and refused by name when they name any other; use
        # SoftSPI to pick your own. They were typed const, so passing a Pin at all
        # failed with a message about constants. baudrate/polarity/phase/firstbit
        # reprogram the real SPCR/SPSR registers via the HAL.
        if id != 0:
            raise _CompileError("machine.SPI: this chip has a single SPI bus; id must be 0.")
        if bits != 8:
            raise _CompileError("machine.SPI: this chip's SPI shifts a fixed 8-bit frame; bits=8 only.")
        _spi_check_pins(sck, mosi, miso)
        # Calls the HAL with firstbit's own value or a literal, never a variable
        # reassigned from it: a const parameter reassigned through a branch stops
        # being a compile-time constant to this compiler.
        if firstbit == SPI.LSB:
            self._spi = _SPI(0, "", baudrate, polarity, phase, 1)
        else:
            self._spi = _SPI(0, "", baudrate, polarity, phase, 0)

    @inline
    def init(self, baudrate: const[uint32] = 1000000, *, polarity: const[uint8] = 0,
             phase: const[uint8] = 0, bits: const[uint8] = 8, firstbit: const[uint8] = 1,
             sck: Pin = None, mosi: Pin = None, miso: Pin = None):
        # Reprogram a bus that is already running (MicroPython standard).
        if bits != 8:
            raise _CompileError("machine.SPI: this chip's SPI shifts a fixed 8-bit frame; bits=8 only.")
        _spi_check_pins(sck, mosi, miso)
        if firstbit == SPI.LSB:
            self._spi.configure(baudrate, polarity, phase, 1)
        else:
            self._spi.configure(baudrate, polarity, phase, 0)

    @inline
    def deinit(self):
        pass

    @inline
    def write(self, buf: uint8):
        # Single-byte write. Upstream's write() takes only a buffer, but a
        # uint8 is the honest one-byte shape on a heap-less target -- the name
        # and arity match, so a ported write(bytearray) call binds the buffer
        # overload below.
        self._spi.write(buf)

    @inline
    def write(self, buf: bytearray):
        # Matches MicroPython: write(buf) transmits len(buf) bytes.
        # len(buf) folds to a compile-time constant from the array's declaration.
        self._spi.write_bytes(buf, len(buf))

    @inline
    def read(self, nbytes: const[uint16], write: uint8 = 0x00) -> bytearray:
        # MicroPython: read(nbytes, write=0x00) returns nbytes clocked in while write is
        # sent. Returned by value, like I2C.readfrom: an @inline method's locals live in
        # the caller's frame. The result is a bytearray where upstream's is bytes.
        buf = bytearray(nbytes)
        self.readinto(buf, write)
        return buf

    @inline
    def readinto(self, buf: bytearray, write: uint8 = 0x00):
        # MicroPython: readinto(buf, write=0, /) fills len(buf) bytes, sending
        # write as the dummy byte on MOSI for each one.
        self._spi.readinto_n(buf, len(buf), write)

    @inline
    def write_readinto(self, write_buf: bytearray, read_buf: bytearray):
        # Matches MicroPython: write_readinto(write_buf, read_buf) infers len from write_buf.
        self._spi.write_readinto_n(write_buf, read_buf, len(write_buf))


# ---------------------------------------------------------------------------
# SoftSPI (bit-bang, MicroPython machine.SoftSPI)
# ---------------------------------------------------------------------------

class SoftSPI:
    # Bit-order constants -- the rp2 port's own values, measured on real
    # firmware (SoftSPI.MSB == SPI.MSB upstream).
    MSB = 1
    LSB = 0

    @inline
    def __init__(self, baudrate: const[uint32] = 500000, *, polarity: const[uint8] = 0,
                 phase: const[uint8] = 0, bits: const[uint8] = 8, firstbit: const[uint8] = 1,
                 sck: Pin = None, mosi: Pin = None, miso: Pin = None):
        # MicroPython: SoftSPI(baudrate=500_000, polarity=0, phase=0, bits=8,
        # firstbit=SPI.MSB, sck=None, mosi=None, miso=None). Bit-banged, so unlike
        # hardware SPI there is no fixed pin set to fall back to: sck=/mosi=/miso= are
        # required. pymcu.hal.softspi.SoftSPI implements mode 0 (polarity=0, phase=0)
        # MSB-first only; anything else is refused by name.
        if bits != 8:
            raise _CompileError("machine.SoftSPI: bit-banged transfer is a fixed 8-bit frame; bits=8 only.")
        if polarity != 0 or phase != 0:
            raise _CompileError("machine.SoftSPI: only mode 0 (polarity=0, phase=0) is implemented.")
        if firstbit == SoftSPI.LSB:
            raise _CompileError("machine.SoftSPI: only MSB-first (firstbit=SoftSPI.MSB) is implemented.")
        if sck is None or mosi is None or miso is None:
            raise _CompileError("machine.SoftSPI: sck=/mosi=/miso= are required; bit-banged SPI has no fixed pins to default to.")
        khz: uint16 = uint16(baudrate // 1000)
        if khz == 0:
            khz = 1
        self._spi = _SoftSPI(sck._pin, mosi._pin, miso._pin, 0, None, khz)

    @inline
    def init(self, baudrate: const[uint32] = 500000, *, polarity: const[uint8] = 0,
             phase: const[uint8] = 0, bits: const[uint8] = 8, firstbit: const[uint8] = 1):
        # Reprogram the clock rate of a bus that is already running (MicroPython
        # standard). Pins cannot be changed after construction here (they are baked
        # into which GPIO registers the bit-bang loop touches).
        if bits != 8:
            raise _CompileError("machine.SoftSPI: bit-banged transfer is a fixed 8-bit frame; bits=8 only.")
        if polarity != 0 or phase != 0:
            raise _CompileError("machine.SoftSPI: only mode 0 (polarity=0, phase=0) is implemented.")
        if firstbit == SoftSPI.LSB:
            raise _CompileError("machine.SoftSPI: only MSB-first (firstbit=SoftSPI.MSB) is implemented.")
        # pymcu.hal.softspi.SoftSPI.set_baudrate() is unreachable here: a compiler bug
        # (PyMCU/PyMCU#453) loses track of a field a match/case branch in __init__
        # assigns, once a class also has a Pin-typed field -- SoftSPI has three. Honest
        # refusal beats calling into a method that miscompiles.
        raise _CompileError("machine.SoftSPI.init: reprogramming the clock rate after construction is blocked by a compiler bug (PyMCU/PyMCU#453). Construct a new SoftSPI at the desired baudrate= instead.")

    @inline
    def deinit(self):
        # Bit-banged: nothing to release. Present for API completeness.
        pass

    @inline
    def write(self, buf: uint8):
        self._spi.write(buf)

    @inline
    def write(self, buf: bytearray):
        i: uint16 = 0
        n: uint16 = len(buf)
        while i < n:
            self._spi.write(buf[i])
            i = i + 1

    @inline
    def read(self, nbytes: const[uint16], write: uint8 = 0x00) -> bytearray:
        # MicroPython: read(nbytes, write=0x00). See SPI.read.
        buf = bytearray(nbytes)
        self.readinto(buf, write)
        return buf

    @inline
    def readinto(self, buf: bytearray, write: uint8 = 0x00):
        # MicroPython: readinto(buf, write=0x00) -- one overload with the
        # upstream default, which is 0x00, not this layer's former 0xFF.
        i: uint16 = 0
        n: uint16 = len(buf)
        while i < n:
            buf[i] = self._spi.transfer(write)
            i = i + 1

    @inline
    def write_readinto(self, write_buf: bytearray, read_buf: bytearray):
        i: uint16 = 0
        n: uint16 = len(write_buf)
        while i < n:
            read_buf[i] = self._spi.transfer(write_buf[i])
            i = i + 1


# ---------------------------------------------------------------------------
# I2C
# ---------------------------------------------------------------------------

class I2C:
    @inline
    def __init__(self, id: const[uint8] = 0, *, scl: Pin = None, sda: Pin = None,
                 freq: const[uint32] = 400000, timeout: const[uint32] = 50000):
        # MicroPython: I2C(id, *, scl, sda, freq=400000, timeout=50000). The default is
        # upstream's 400 kHz (machine.I2C.rst, and DEFAULT_I2C_FREQ in the rp2 port); it
        # was 100 kHz here. The HAL's own default stays 100 kHz, which is what
        # CircuitPython's busio.I2C asks for. The TWI pins are
        # fixed in silicon (PC5 = SCL, PC4 = SDA), so scl=/sda= are accepted when they
        # name those pins -- I2C(0, scl=Pin(19), sda=Pin(18)) on an Uno, the way a port
        # spells its bus -- and refused by name when they name any other. freq programs
        # the bit-rate register (the HAL refuses what the TWI cannot reach). The bus
        # timeout is the HAL's own fixed guard, so only the default is accepted.
        if id != 0:
            raise _CompileError("machine.I2C: this chip has a single TWI bus; id must be 0.")
        if scl is not None:
            if scl._name != "PC5":
                raise _CompileError("machine.I2C: the TWI pins are fixed on this chip; SCL is PC5 (Pin(19) on an Uno). Use SoftI2C to pick your own pins.")
        if sda is not None:
            if sda._name != "PC4":
                raise _CompileError("machine.I2C: the TWI pins are fixed on this chip; SDA is PC4 (Pin(18) on an Uno). Use SoftI2C to pick your own pins.")
        if timeout != 50000:
            raise _CompileError("machine.I2C: the bus timeout is fixed on this chip; drop the timeout argument.")
        self._i2c = _I2C(0, 0, freq)

    @inline
    def scan(self) -> uint8:
        # MicroPython's scan() returns a heap-allocated list of addresses,
        # which this target cannot build. Answering with a count would hand a
        # ported `for addr in i2c.scan()` an integer instead -- refuse and name
        # the caller-owned-buffer form.
        raise _CompileError("machine.I2C.scan: upstream returns a heap-allocated list of addresses, which this target cannot build. Fill a caller-owned buffer instead: found = i2c.scan(buf, len(buf)).")

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
    def writeto(self, addr: uint8, buf: uint8, stop: uint8 = 1):
        # MicroPython: writeto(addr, buf, stop=True, /) -- stop=False holds the bus with
        # a repeated START instead of releasing it, for a following readfrom*(). `stop`
        # is a plain (not keyword-only) parameter: the real stub marks it
        # positional-only, and MicroPython code calls it that way in practice, which
        # also keeps a keyword call from ever reaching a name with more than one
        # @inline overload (PyMCU/PyMCU#447). The single-byte overload spells the
        # parameter buf like upstream's; a uint8 is the honest one-byte shape on a
        # heap-less target.
        # A NACK raises OSError [Errno 5] EIO, the way the rp2 port reports it -- the
        # status used to be ignored, so a dead bus looked exactly like a live one and
        # a try/except OSError around the call never ran.
        if stop:
            if self._i2c.writebyte(addr, buf) != 1:
                raise OSError("[Errno 5] EIO")
        else:
            st: uint8 = self._i2c.start()
            if st != _I2C.START and st != _I2C.RESTART:
                self._i2c.stop()
                raise OSError("[Errno 5] EIO")
            if self._i2c.write(addr << 1) != _I2C.SLA_ACK:
                self._i2c.stop()
                raise OSError("[Errno 5] EIO")
            if self._i2c.write(buf) != _I2C.DATA_ACK:
                self._i2c.stop()
                raise OSError("[Errno 5] EIO")

    @inline
    def writeto(self, addr: uint8, buf: bytearray, stop: uint8 = 1):
        # Matches MicroPython: writeto(addr, buf) sends len(buf) bytes.
        if stop:
            if self._i2c.write_bytes(addr, buf, len(buf)) != 1:
                raise OSError("[Errno 5] EIO")
        else:
            st: uint8 = self._i2c.start()
            if st != _I2C.START and st != _I2C.RESTART:
                self._i2c.stop()
                raise OSError("[Errno 5] EIO")
            if self._i2c.write(addr << 1) != _I2C.SLA_ACK:
                self._i2c.stop()
                raise OSError("[Errno 5] EIO")
            i: uint16 = 0
            n: uint16 = len(buf)
            while i < n:
                if self._i2c.write(buf[i]) != _I2C.DATA_ACK:
                    self._i2c.stop()
                    raise OSError("[Errno 5] EIO")
                i = i + 1

    @inline
    def _writevto_part(self, part) -> uint16:
        # One buffer of a writevto() vector, inside the transaction writevto opened.
        i: uint16 = 0
        n: uint16 = len(part)
        while i < n:
            if self._i2c.write(part[i]) != _I2C.DATA_ACK:
                self._i2c.stop()
                raise OSError("[Errno 5] EIO")
            i = i + 1
        return n

    @inline
    def writevto(self, addr: uint8, vector, stop: uint8 = 1) -> uint16:
        # MicroPython: writevto(addr, vector, stop=True, /) writes every buffer of
        # vector, in order, as one transaction -- one START and one address, then the
        # bytes of each buffer back to back -- and returns the number of ACKs. The
        # SSD1306 driver sends its data prefix and the framebuffer this way. A NACK
        # raises OSError EIO like writeto. stop=False holds the bus for a repeated START.
        #
        # The vector is walked by literal index because `for part in vector` over a
        # sequence of buffers is refused by the compiler (it walks sequences of integer
        # constants only). Eight buffers is the most this spells out; more is refused.
        if len(vector) > 8:
            raise _CompileError("machine.I2C.writevto: at most 8 buffers in the vector on this target.")
        st: uint8 = self._i2c.start()
        if st != _I2C.START and st != _I2C.RESTART:
            self._i2c.stop()
            raise OSError("[Errno 5] EIO")
        if self._i2c.write(addr << 1) != _I2C.SLA_ACK:
            self._i2c.stop()
            raise OSError("[Errno 5] EIO")
        acks: uint16 = 0
        if len(vector) > 0:
            acks = acks + self._writevto_part(vector[0])
        if len(vector) > 1:
            acks = acks + self._writevto_part(vector[1])
        if len(vector) > 2:
            acks = acks + self._writevto_part(vector[2])
        if len(vector) > 3:
            acks = acks + self._writevto_part(vector[3])
        if len(vector) > 4:
            acks = acks + self._writevto_part(vector[4])
        if len(vector) > 5:
            acks = acks + self._writevto_part(vector[5])
        if len(vector) > 6:
            acks = acks + self._writevto_part(vector[6])
        if len(vector) > 7:
            acks = acks + self._writevto_part(vector[7])
        if stop:
            self._i2c.stop()
        return acks

    @inline
    def readfrom(self, addr: uint8, nbytes: const[uint16], stop: uint8 = 1) -> bytearray:
        # MicroPython: readfrom(addr, nbytes, stop=True, /) returns nbytes read from the
        # peripheral. There is no heap, but an @inline method's locals live in the
        # caller's frame, so a buffer of a compile-time size is returned by value.
        # Upstream's result is an immutable bytes; this one is a bytearray.
        buf = bytearray(nbytes)
        self.readfrom_into(addr, buf, stop)
        return buf

    @inline
    def readfrom_into(self, addr: uint8, buf: bytearray, stop: uint8 = 1) -> uint8:
        # Matches MicroPython: readfrom_into(addr, buf, stop=True, /) fills len(buf)
        # bytes and raises OSError [Errno 5] EIO on a NACK. stop=False leaves the bus
        # held for a following operation.
        if stop:
            if self._i2c.read_n(addr, buf, len(buf)) != 1:
                raise OSError("[Errno 5] EIO")
            return 1
        st: uint8 = self._i2c.start()
        if st != _I2C.START and st != _I2C.RESTART:
            self._i2c.stop()
            raise OSError("[Errno 5] EIO")
        if self._i2c.write((addr << 1) | 1) != _I2C.SLA_R_ACK:
            self._i2c.stop()
            raise OSError("[Errno 5] EIO")
        i: uint16 = 0
        n: uint16 = len(buf)
        while i < n:
            if i == n - 1:
                buf[i] = self._i2c.read_nack()
            else:
                buf[i] = self._i2c.read_ack()
            i = i + 1
        return 1

    @inline
    def start(self):
        # MicroPython: start(). Raw primitive for manually-sequenced transactions.
        self._i2c.start()

    @inline
    def stop(self):
        self._i2c.stop()

    @inline
    def write(self, buf: bytearray) -> uint16:
        # MicroPython: write(buf) writes buf during a manually start()/stop()-sequenced
        # transaction. Returns the number of ACKs received -- one per byte, so a buffer
        # longer than 255 needs a count wider than a byte to report it.
        acks: uint16 = 0
        i: uint16 = 0
        n: uint16 = len(buf)
        while i < n:
            status: uint8 = self._i2c.write(buf[i])
            if status == 0x18 or status == 0x28:
                acks = acks + 1
            i = i + 1
        return acks

    @inline
    def readinto(self, buf: bytearray, nack: uint8 = 1):
        # MicroPython: readinto(buf, nack=True, /). nack=True (the normal case) sends
        # NACK after the last byte; nack=False sends ACK even for the last byte, for a
        # read that will be followed by more reads before stop().
        i: uint16 = 0
        n: uint16 = len(buf)
        while i < n:
            if i == n - 1 and nack:
                buf[i] = self._i2c.read_nack()
            else:
                buf[i] = self._i2c.read_ack()
            i = i + 1

    @inline
    def writeto_mem(self, addr: uint8, memaddr: uint8, buf: bytearray, *, addrsize: const[uint8] = 8) -> uint8:
        # MicroPython: writeto_mem(addr, memaddr, buf, /, *, addrsize=8). This chip's
        # TWI addresses an 8-bit register; addrsize is accepted and refused for
        # anything else instead of silently ignored.
        if addrsize != 8:
            raise _CompileError("machine.I2C.writeto_mem: only 8-bit register addresses (addrsize=8) are supported on this chip.")
        if len(buf) == 1:
            if self._i2c.writeto_mem(addr, memaddr, buf[0]) != 1:
                raise OSError("[Errno 5] EIO")
            return 1
        st: uint8 = self._i2c.start()
        if st != _I2C.START and st != _I2C.RESTART:
            self._i2c.stop()
            raise OSError("[Errno 5] EIO")
        if self._i2c.write(addr << 1) != _I2C.SLA_ACK:
            self._i2c.stop()
            raise OSError("[Errno 5] EIO")
        if self._i2c.write(memaddr) != _I2C.DATA_ACK:
            self._i2c.stop()
            raise OSError("[Errno 5] EIO")
        i: uint16 = 0
        n: uint16 = len(buf)
        while i < n:
            if self._i2c.write(buf[i]) != _I2C.DATA_ACK:
                self._i2c.stop()
                raise OSError("[Errno 5] EIO")
            i = i + 1
        self._i2c.stop()
        return 1

    @inline
    def readfrom_mem_into(self, addr: uint8, memaddr: uint8, buf: bytearray, *, addrsize: const[uint8] = 8) -> uint8:
        # MicroPython: readfrom_mem_into(addr, memaddr, buf, /, *, addrsize=8).
        if addrsize != 8:
            raise _CompileError("machine.I2C.readfrom_mem_into: only 8-bit register addresses (addrsize=8) are supported on this chip.")
        if self._i2c.readfrom_mem(addr, memaddr, buf, len(buf)) != 1:
            raise OSError("[Errno 5] EIO")
        return 1

    @inline
    def readfrom_mem(self, addr: uint8, memaddr: uint8, nbytes: const[uint16], *,
                     addrsize: const[uint8] = 8) -> bytearray:
        # MicroPython: readfrom_mem(addr, memaddr, nbytes, *, addrsize=8) returns nbytes
        # read from register memaddr. Returned by value like readfrom(); the result is a
        # bytearray where upstream's is bytes. This used to be a four-argument PyMCU
        # extension taking a caller buffer, so the upstream call did not compile; that
        # form is readfrom_mem_into(addr, memaddr, buf).
        buf = bytearray(nbytes)
        self.readfrom_mem_into(addr, memaddr, buf, addrsize=addrsize)
        return buf


# ---------------------------------------------------------------------------
# SoftI2C: bit-bang I2C on any two pins
# ---------------------------------------------------------------------------

class SoftI2C:
    @inline
    def __init__(self, scl: Pin, sda: Pin, freq: const[uint32] = 400000):
        # MicroPython: SoftI2C(scl, sda, *, freq=400000, timeout=50000); the default is
        # upstream's 400 kHz, which the docs define as the MAXIMUM SCL rate (the real
        # one may be lower). Both lines need external pull-ups. The half-period is a
        # whole number of microseconds derived from freq at compile time, so the rate
        # this bit-bang reaches at 16 MHz is lower than asked: measured on the emulator,
        # 100 kHz runs at about 82 kHz and 400 kHz (a 1 us half-period) at about 235 kHz;
        # freq >= 500 kHz drops the delays entirely, about 800 kHz.
        half: uint8 = uint8(500000 // freq)
        self._bus = _SoftI2C(scl._pin, sda._pin, half)
        self._bus.init()

    @inline
    def scan(self) -> uint8:
        # MicroPython's scan() returns a heap-allocated list of addresses,
        # which this target cannot build -- same refusal as I2C.scan. Fill a
        # caller-owned buffer instead: found = i2c.scan(buf, len(buf)).
        raise _CompileError("machine.SoftI2C.scan: upstream returns a heap-allocated list of addresses, which this target cannot build. Fill a caller-owned buffer instead: found = i2c.scan(buf, len(buf)).")

    @inline
    def scan(self, buf: bytearray, max_count: uint8) -> uint8:
        # Scans addresses 0x01-0x7F; stores each responding address in buf.
        # Returns the number of devices found (up to max_count).
        # Deviation: MicroPython scan() returns a list; PyMCU uses caller-owned buffer.
        count: uint8 = 0
        addr: uint8 = 1
        while addr < 128:
            if self._bus.ping(addr):
                if count < max_count:
                    buf[count] = addr
                    count = count + 1
            addr = addr + 1
        return count

    @inline
    def writeto(self, addr: uint8, buf: uint8, stop: uint8 = 1):
        # See machine.I2C.writeto: stop is a plain (not keyword-only) parameter on
        # purpose (PyMCU/PyMCU#447). A NACK raises OSError [Errno 5] EIO like the
        # hardware bus does; the bit-banged HAL reports it as a nonzero ACK bit.
        if stop:
            if self._bus.write_to(addr, buf) != 1:
                raise OSError("[Errno 5] EIO")
        else:
            self._bus.start()
            if self._bus.write(addr << 1) != 0:
                self._bus.stop()
                raise OSError("[Errno 5] EIO")
            if self._bus.write(buf) != 0:
                self._bus.stop()
                raise OSError("[Errno 5] EIO")

    @inline
    def writeto(self, addr: uint8, buf: bytearray, stop: uint8 = 1):
        # Matches MicroPython: writeto(addr, buf) sends len(buf) bytes.
        if stop:
            if self._bus.write_bytes(addr, buf, len(buf)) != 1:
                raise OSError("[Errno 5] EIO")
        else:
            self._bus.start()
            if self._bus.write(addr << 1) != 0:
                self._bus.stop()
                raise OSError("[Errno 5] EIO")
            i: uint16 = 0
            n: uint16 = len(buf)
            while i < n:
                if self._bus.write(buf[i]) != 0:
                    self._bus.stop()
                    raise OSError("[Errno 5] EIO")
                i = i + 1

    @inline
    def _writevto_part(self, part) -> uint16:
        i: uint16 = 0
        n: uint16 = len(part)
        while i < n:
            if self._bus.write(part[i]) != 0:
                self._bus.stop()
                raise OSError("[Errno 5] EIO")
            i = i + 1
        return n

    @inline
    def writevto(self, addr: uint8, vector, stop: uint8 = 1) -> uint16:
        # MicroPython: writevto(addr, vector, stop=True, /). See I2C.writevto.
        if len(vector) > 8:
            raise _CompileError("machine.SoftI2C.writevto: at most 8 buffers in the vector on this target.")
        self._bus.start()
        if self._bus.write(addr << 1) != 0:
            self._bus.stop()
            raise OSError("[Errno 5] EIO")
        acks: uint16 = 0
        if len(vector) > 0:
            acks = acks + self._writevto_part(vector[0])
        if len(vector) > 1:
            acks = acks + self._writevto_part(vector[1])
        if len(vector) > 2:
            acks = acks + self._writevto_part(vector[2])
        if len(vector) > 3:
            acks = acks + self._writevto_part(vector[3])
        if len(vector) > 4:
            acks = acks + self._writevto_part(vector[4])
        if len(vector) > 5:
            acks = acks + self._writevto_part(vector[5])
        if len(vector) > 6:
            acks = acks + self._writevto_part(vector[6])
        if len(vector) > 7:
            acks = acks + self._writevto_part(vector[7])
        if stop:
            self._bus.stop()
        return acks

    @inline
    def readfrom(self, addr: uint8, nbytes: const[uint16], stop: uint8 = 1) -> bytearray:
        # MicroPython: readfrom(addr, nbytes, stop=True, /). See I2C.readfrom.
        buf = bytearray(nbytes)
        self.readfrom_into(addr, buf, stop)
        return buf

    @inline
    def readfrom_into(self, addr: uint8, buf: bytearray, stop: uint8 = 1) -> uint8:
        # Matches MicroPython: readfrom_into(addr, buf, stop=True, /) fills len(buf)
        # bytes and raises OSError [Errno 5] EIO on a NACK.
        self._bus.start()
        if self._bus.write((addr << 1) | 1) != 0:
            self._bus.stop()
            raise OSError("[Errno 5] EIO")
        i: uint16 = 0
        n: uint16 = len(buf)
        while i < n:
            if i == n - 1:
                buf[i] = self._bus.read(0)
            else:
                buf[i] = self._bus.read(1)
            i = i + 1
        if stop:
            self._bus.stop()
        return 1

    @inline
    def start(self):
        self._bus.start()

    @inline
    def stop(self):
        self._bus.stop()

    @inline
    def write(self, buf: bytearray) -> uint16:
        # MicroPython: write(buf) writes buf during a manually start()/stop()-sequenced
        # transaction. Returns the number of ACKs received -- one per byte, so a buffer
        # longer than 255 needs a count wider than a byte to report it.
        acks: uint16 = 0
        i: uint16 = 0
        n: uint16 = len(buf)
        while i < n:
            if self._bus.write(buf[i]) == 0:
                acks = acks + 1
            i = i + 1
        return acks

    @inline
    def readinto(self, buf: bytearray, nack: uint8 = 1):
        # MicroPython: readinto(buf, nack=True, /).
        i: uint16 = 0
        n: uint16 = len(buf)
        while i < n:
            if i == n - 1 and nack:
                buf[i] = self._bus.read(0)
            else:
                buf[i] = self._bus.read(1)
            i = i + 1

    @inline
    def writeto_mem(self, addr: uint8, memaddr: uint8, buf: bytearray, *, addrsize: const[uint8] = 8) -> uint8:
        # MicroPython: writeto_mem(addr, memaddr, buf, /, *, addrsize=8).
        if addrsize != 8:
            raise _CompileError("machine.SoftI2C.writeto_mem: only 8-bit register addresses (addrsize=8) are supported on this chip.")
        self._bus.start()
        if self._bus.write(addr << 1) != 0:
            self._bus.stop()
            raise OSError("[Errno 5] EIO")
        if self._bus.write(memaddr) != 0:
            self._bus.stop()
            raise OSError("[Errno 5] EIO")
        i: uint16 = 0
        n: uint16 = len(buf)
        while i < n:
            if self._bus.write(buf[i]) != 0:
                self._bus.stop()
                raise OSError("[Errno 5] EIO")
            i = i + 1
        self._bus.stop()
        return 1

    @inline
    def readfrom_mem_into(self, addr: uint8, memaddr: uint8, buf: bytearray, *, addrsize: const[uint8] = 8) -> uint8:
        # MicroPython: readfrom_mem_into(addr, memaddr, buf, /, *, addrsize=8).
        if addrsize != 8:
            raise _CompileError("machine.SoftI2C.readfrom_mem_into: only 8-bit register addresses (addrsize=8) are supported on this chip.")
        self._bus.start()
        if self._bus.write(addr << 1) != 0:
            self._bus.stop()
            raise OSError("[Errno 5] EIO")
        if self._bus.write(memaddr) != 0:
            self._bus.stop()
            raise OSError("[Errno 5] EIO")
        self._bus.start()
        if self._bus.write((addr << 1) | 1) != 0:
            self._bus.stop()
            raise OSError("[Errno 5] EIO")
        i: uint16 = 0
        n: uint16 = len(buf)
        while i < n:
            if i == n - 1:
                buf[i] = self._bus.read(0)
            else:
                buf[i] = self._bus.read(1)
            i = i + 1
        self._bus.stop()
        return 1

    @inline
    def readfrom_mem(self, addr: uint8, memaddr: uint8, nbytes: const[uint16], *,
                     addrsize: const[uint8] = 8) -> bytearray:
        # MicroPython: readfrom_mem(addr, memaddr, nbytes, *, addrsize=8). See
        # I2C.readfrom_mem.
        buf = bytearray(nbytes)
        self.readfrom_mem_into(addr, memaddr, buf, addrsize=addrsize)
        return buf


# ---------------------------------------------------------------------------
# freq: CPU clock frequency
# ---------------------------------------------------------------------------

@inline
def freq() -> uint32:
    # Returns the CPU clock frequency in Hz (compile-time constant from pyproject.toml).
    return __FREQ__


@inline
def unique_id() -> uint8:
    # ATmega328P has no factory-programmed unique ID, so there is nothing
    # honest to return. Erroring beats handing back a fake constant that a
    # ported sketch would use as a device address.
    raise _CompileError("machine.unique_id: this chip has no unique hardware ID (the ATmega328P signature row is the same for every part). Store an ID in EEPROM via the avr module instead.")


# ---------------------------------------------------------------------------
# IRQ control
# ---------------------------------------------------------------------------

@inline
def disable_irq() -> uint8:
    # MicroPython: disable_irq() returns the previous IRQ state, an opaque value to
    # hand back to enable_irq(). It used to return 1 whatever the state was, so a
    # nested section's enable_irq(s2) switched interrupts back on while the outer
    # section still held them off (PyMCU#353).
    return _save_and_disable_interrupts()


@inline
def enable_irq(state: uint8):
    # MicroPython: enable_irq(state) restores the state disable_irq() returned. The
    # argument is required upstream, and it restores: a state taken with interrupts
    # off leaves them off.
    _restore_interrupts(state)


# ---------------------------------------------------------------------------
# Power / sleep
# ---------------------------------------------------------------------------

@inline
def reset():
    # Soft reset: jump to address 0 to re-run the startup stub.
    asm("jmp 0")


@inline
def reset_cause() -> uint8:
    # MicroPython's reset_cause(). The rp2 port answers only PWRON_RESET (1) or
    # WDT_RESET (3); AVR keeps the reason in the MCU status register, whose
    # WDRF bit survives the reset -- so a watchdog restart (including
    # soft_reset()'s) reports WDT_RESET and every other cause (power-on,
    # external pin, brown-out) reports PWRON_RESET. MCUSR sits at data address
    # 0x54 on every AVR the HAL covers.
    if __CHIP__.arch == "avr":
        mcusr: ptr[uint8] = ptr(0x54)
        if mcusr.value & 0x08 != 0:
            return WDT_RESET
        return PWRON_RESET
    else:
        raise _CompileError("machine.reset_cause: no reset-cause register is wired up for this architecture.")


@inline
def soft_reset():
    # A watchdog-triggered restart, unlike reset()'s direct jump to address 0:
    # the WDT firing is a real hardware reset, so every peripheral (UART baud
    # rate, PWM duty, ADC prescaler, ...) comes back to its power-on default
    # instead of resuming main() with whatever state reset() left it in.
    # Arm the shortest timeout (~16 ms) and wait for it -- there is no
    # "trigger now" bit on this chip's watchdog.
    wdt = _Watchdog(16)
    wdt.enable()
    while True:
        pass


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
    # Mode constants -- the rp2 port's own values. The IRQ_OVF/IRQ_COMPA trigger
    # selectors and irq()/start() methods this class used to carry are PyMCU HAL
    # spellings, not upstream: the rp2 Timer attaches its callback through
    # init(callback=...) and has no irq() or start() at all.
    ONE_SHOT  = 0
    PERIODIC  = 1

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
                self._t.irq(callback, _Timer.IRQ_COMPA)
            _enable_interrupts()
        elif period != 0:
            if period > 4369:
                raise _CompileError("machine.Timer: period must be 1-4369 ms on this chip; above that 15 * period overflows the 16-bit compare register and the timer fires at a wrong, much shorter interval. Count several ticks in the callback for longer intervals.")
            if period <= 262:
                self._t.reinit(64)
                ocr: uint16 = uint16(250 * period - 1)
            else:
                self._t.reinit(1024)
                ocr: uint16 = uint16(15 * period)
            self._t.set_compare(ocr)
            if callback != 0:
                self._t.irq(callback, _Timer.IRQ_COMPA)
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
    def __del__(self):
        # MicroPython 1.21's rp2 Timer has __del__; PyMCU never collects, so this
        # only ever runs when a program spells del t explicitly.
        self._t.stop()


# ---------------------------------------------------------------------------
# WDT (Watchdog Timer)
# ---------------------------------------------------------------------------

class WDT:
    @inline
    def __init__(self, id: const[uint8] = 0, timeout: uint16 = 5000):
        # timeout is in milliseconds (MicroPython convention).
        if id != 0:
            raise _CompileError("machine.WDT: this chip has a single watchdog; id must be 0.")
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
    def __init__(self, pin, mode: const = None, pull: const = None, *, invert: const[uint8] = 0):
        # MicroPython: Signal(pin_obj, invert=False) wraps a Pin, and
        # Signal(pin_arguments..., *, invert=False) builds the Pin from the arguments a
        # Pin takes: Signal(13, Pin.OUT, invert=True). One constructor rather than an
        # overload per shape, because a name with more than one @inline overload cannot
        # take a keyword argument (PyMCU#447), and invert= is how both shapes are called.
        # For the Pin-object form the second positional is upstream's invert.
        # invert: 0 = active-high (default), 1 = active-low.
        if isinstance(pin, Pin):
            if pull is not None:
                raise _CompileError("machine.Signal: Signal(pin_obj, invert=False) takes at most two arguments.")
            self._pin = pin
            if mode is None:
                self._inv = invert
            else:
                self._inv = mode
        else:
            if mode is None:
                self._pin = Pin(pin)
            elif pull is None:
                self._pin = Pin(pin, mode)
            else:
                self._pin = Pin(pin, mode, 0 if pull is None else pull)
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
    def value(self) -> uint8:
        # Read the logical (active) value: 1 if the signal is active, 0 if
        # inactive. Two real overloads (get by arity), not a sentinel
        # default -- the same 255-collides-with-255 bug value(x)'s own
        # rewrite above fixed.
        raw: uint8 = self._pin.value()
        if self._inv:
            return 1 - raw
        return raw

    @inline
    def value(self, x: uint8):
        # Write: drives pin to produce the requested logical level. Upstream's
        # signal_call returns None on the write path, same as Pin.value(x).
        if self._inv:
            self._pin.value(1 - x)
        else:
            self._pin.value(x)


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


class _Mem32:
    @inline
    def __getitem__(self, addr: uint16) -> uint32:
        p: ptr[uint32] = ptr(addr)
        return p.value

    @inline
    def __setitem__(self, addr: uint16, value: uint32):
        p: ptr[uint32] = ptr(addr)
        p.value = value


mem8  = _Mem8()
mem16 = _Mem16()
mem32 = _Mem32()

