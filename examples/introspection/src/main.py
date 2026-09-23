# Introspection guards -- MicroPython style
#
# Demonstrates the compile-time introspection the layer provides:
#   sys.implementation.name / .version[i]   (and the usys spelling)
#   sys.platform                            (and usys.platform)
#   os.uname().field / membership           (and uos.uname())
#
# Every check below is answered by the compiler at build time -- a compiled
# program carries no runtime tuple, stream, or module table. The values are
# real per-board answers (see README "os and sys"), not the CPython
# placeholders the layer files carry for IDEs.
#
# Expected behaviour (atmega328p, board = arduino_uno):
#   sys.platform is the chip name ("atmega328p" -- no upstream port exists)
#   on an RP2040 board it would be "rp2" instead, unchanged source.

import sys
import usys
import os
import uos
from machine import Pin

# Both spellings, condition position -- the interpreter-identity guard.
if sys.implementation.name == "micropython" and usys.implementation.name == "micropython":
    led = Pin(13, Pin.OUT)
    led.on()

# version tuple, indexed -- the feature-presence guard.
if sys.implementation.version[0] >= 1 and usys.implementation.version[0] >= 1:
    led.off()

# platform + uname fields and membership, in conditions.
if sys.platform != "win32" and usys.platform != "win32":
    led.toggle()

if os.uname().sysname != "" and uos.uname().machine != "":
    led.toggle()

if "Linux" not in os.uname() and "Linux" not in uos.uname() and "Linux" not in uname():
    led.toggle()

# Bare reads -- the compiler substitutes the same per-board values.
p = sys.platform
q = usys.platform
n = sys.implementation.name
v = sys.implementation.version[0]
s = uos.uname().sysname
m = uos.uname().machine


def main():
    while True:
        led.toggle()
