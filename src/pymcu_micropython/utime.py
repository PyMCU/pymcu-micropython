# MicroPython-compatible utime module for PyMCU
#
# Provides sleep_ms(), sleep_us(), and ticks_ms() that map to the underlying
# PyMCU delay functions (no runtime overhead).
#
# Usage:
#   from utime import sleep_ms, sleep_us
#   sleep_ms(500)
#   sleep_us(100)

from pymcu.types import uint8, uint16, uint32, inline
from pymcu.time import delay_ms, delay_us


@inline
def sleep_ms(ms: uint16):
    delay_ms(ms)


@inline
def sleep_us(us: uint8):
    delay_us(us)


@inline
def sleep(seconds: uint16):
    # MicroPython sleep() takes a float; on MCUs we use integer seconds.
    delay_ms(seconds * 1000)


@inline
def ticks_ms() -> uint32:
    # Returns elapsed milliseconds since millis_init() was called.
    # millis_init() is auto-injected by the build driver when ticks_ms() usage
    # is detected in user code -- no explicit setup required.
    from pymcu.hal.timer import millis
    return millis()


@inline
def ticks_diff(new_ticks: uint32, old_ticks: uint32) -> uint32:
    return new_ticks - old_ticks
