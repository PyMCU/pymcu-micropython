# MicroPython-compatible uasyncio module for PyMCU
#
# In MicroPython, 'asyncio' and 'uasyncio' are the same module, and 'uasyncio' is the spelling
# a large part of the existing code base uses: it is what every pre-1.13 tutorial shows. The
# 'u' spelling had nothing to resolve to here, so `import uasyncio as asyncio` was reported as
# a missing third-party library and the advice sent the reader to `pymcu install uasyncio`,
# which cannot succeed because uasyncio is not a library in the index.
#
# This alias re-exports the PyMCU asyncio surface unchanged. The same pairing already exists
# for time and utime.
#
#   import uasyncio as asyncio    # canonical pre-1.13 MicroPython
#   import asyncio                # also valid, and what MicroPython settled on

from pymcu.asyncio import ticks, sleep, sleep_ms, run, gather
