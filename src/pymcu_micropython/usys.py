# MicroPython-compatible usys module for PyMCU
#
# Upstream, `usys` is the same module as `sys` under its u-prefix name (the
# micropython-stdlib-stubs usys.pyi is literally `from sys import *`), so this
# file re-exports the whole of this layer's sys.py -- `implementation` and
# `platform`. See sys.py for why those are the only members and how the
# compiler answers them.
#
# The relative import is deliberate: under pymcuc `usys` is a top-level module
# and `.sys` resolves to the sibling file; under CPython the layer is the
# package `pymcu_micropython` and `.sys` resolves to pymcu_micropython.sys. A
# bare `from sys import ...` would find CPython's real sys instead and hand
# the parity suite an interpreter's answers it should never see.
from .sys import implementation, platform
