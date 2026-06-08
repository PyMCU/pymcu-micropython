# MicroPython-compatible time module for PyMCU
#
# In MicroPython, 'time' and 'utime' are the same module.
# This alias lets user code use either spelling:
#   from utime import sleep_ms   # canonical MicroPython
#   from time import sleep_ms    # also valid in MicroPython

from pymcu.types import uint16, uint32, inline
from pymcu.time import delay_ms, delay_us


@inline
def sleep_ms(ms: uint16):
    delay_ms(ms)


@inline
def sleep_us(us: uint16):
    delay_us(us)


@inline
def sleep(seconds: uint16):
    delay_ms(seconds * 1000)


@inline
def ticks_ms() -> uint32:
    from pymcu.hal.timer import millis
    return millis()


@inline
def ticks_us() -> uint32:
    from pymcu.hal.timer import micros
    return micros()


@inline
def ticks_cpu() -> uint32:
    from pymcu.hal.timer import micros
    return micros()


@inline
def ticks_diff(new_ticks: uint32, old_ticks: uint32) -> uint32:
    return new_ticks - old_ticks


@inline
def ticks_add(ticks: uint32, delta: uint32) -> uint32:
    return ticks + delta
