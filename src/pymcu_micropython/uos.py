# MicroPython-compatible uos module for PyMCU
#
# Upstream, `uos` is the same module as `os` under its u-prefix name (the
# micropython-stdlib-stubs uos.pyi is literally `from os import *`), so this
# file re-exports the whole of this layer's os.py -- which is `uname()`. See
# os.py for why that is the only member and how the compiler answers it.
#
# The relative import is deliberate: under pymcuc `uos` is a top-level module
# and `.os` resolves to the sibling file; under CPython the layer is the
# package `pymcu_micropython` and `.os` resolves to pymcu_micropython.os. A
# bare `from os import uname` would find CPython's real os instead and hand
# the parity suite a POSIX uname it should never see.
from .os import uname
