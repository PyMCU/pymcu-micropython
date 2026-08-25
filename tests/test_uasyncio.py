"""
uasyncio is the same module as asyncio (PyMCU#113).

`uasyncio` is the spelling most of the existing MicroPython code base uses, and the one every
pre-1.13 tutorial shows. Without this alias it was reported as a missing third-party library,
with advice to run `pymcu install uasyncio`, which cannot succeed: uasyncio is not a library
in the index, it is a name for a module PyMCU already has.
"""
import pymcu.asyncio as _canonical
from pymcu_micropython import uasyncio


def test_every_name_the_canonical_module_exports_is_here():
    for name in ("ticks", "sleep", "sleep_ms", "run", "gather"):
        assert hasattr(uasyncio, name), f"uasyncio is missing {name}"


def test_the_names_are_the_same_objects_not_reimplementations():
    # An alias, not a second implementation that can drift from the first.
    for name in ("ticks", "sleep", "sleep_ms", "run", "gather"):
        assert getattr(uasyncio, name) is getattr(_canonical, name)
