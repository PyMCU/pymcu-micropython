# MicroPython-compatible utime module for Whipsnake
#
# Provides sleep_ms(), sleep_us(), and ticks_ms() that map to the underlying
# Whipsnake delay functions (no runtime overhead).
#
# Usage:
#   from utime import sleep_ms, sleep_us
#   sleep_ms(500)
#   sleep_us(100)

from whipsnake.types import uint8, uint16, inline
from whipsnake.time import delay_ms, delay_us


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
def ticks_ms() -> uint16:
    # Stub: no hardware timestamp without a free-running timer.
    # Returns 0. Use Timer0/1/2 + @interrupt for real timestamps.
    return 0


@inline
def ticks_diff(new_ticks: uint16, old_ticks: uint16) -> uint16:
    # Stub: returns difference (works for 0-based stubs).
    return new_ticks - old_ticks
