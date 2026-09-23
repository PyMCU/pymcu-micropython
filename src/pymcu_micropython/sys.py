# MicroPython-compatible sys module for PyMCU
#
# `sys.implementation.name`, `sys.implementation.version` and `sys.platform` are
# provided, because that is the whole of `sys` the MicroPython library ecosystem
# reaches for at import/branch time to tell ports apart (PyMCU docs/rfcs/0007:
# `if sys.platform == "rp2":` / `if sys.implementation.name == "micropython":`
# are the two shapes the CircuitPython-side survey found MicroPython libraries
# write, mirrored here for the same reason the CircuitPython flavor exists).
#
# The rest of MicroPython's sys -- argv, byteorder, exit(), maxsize, modules,
# path, print_exception, stdin, stdout, stderr, version, version_info -- is NOT
# here. Every one of them needs a runtime PyMCU does not have (a module table,
# a filesystem, a stream object) or reports an interpreter build there is no
# interpreter to report on, and a name that exists here but not on a board is
# the failure this layer exists to prevent.
#
# Why the value is "micropython": a program built against this layer is meant
# to be the same program that runs under MicroPython, so the guards libraries
# write to tell interpreters apart have to fold the way they fold on a board.
# The CircuitPython flavor answers "circuitpython" from its own sys for the
# same reason: the identity follows the layer, because the layer is the claim.
#
# COMPILE-TIME CONSTANTS. `sys.implementation.name`, `sys.implementation.version`
# (and its indexing, `version[0]`) and `sys.platform` are resolved and
# substituted by the compiler at the point they are read, exactly the way
# `__CHIP__.arch` is (see pymcu.chips): the compiler folds the branch away
# before code generation. The values below are placeholders for IDEs and for
# `import pymcu_micropython.sys` under plain CPython (this layer's own parity
# suite) -- a compiled program never actually reads this file's globals. The
# real per-board values are in docs/rfcs/0007 in the PyMCU repo:
#
#   sys.implementation.version is (1, 29, 0) on every board this layer
#   supports, because that is the MicroPython API surface pymcu-micropython's
#   own parity suite is pinned against (micropython-rp2-stubs>=1.29.0.post1),
#   not this package's own 0.x version. Bumping it is a deliberate act tied to
#   re-running the parity suite against a newer stub package, not a side
#   effect of a package release.
#
#   sys.platform is MicroPython's own port short name where one exists ("rp2"
#   on the Pico and the Pico 2 -- MicroPython's rp2 port answers "rp2" for
#   both RP2040 and RP2350, not the MCU name) and the plain chip name where it
#   does not (every AVR part, CH32V003 -- MicroPython has never had an
#   upstream port for either): honest, since no such board is really "rp2" or
#   "samd" and a guard comparing against one of those should take its generic
#   (false) branch.
#
# Usage:
#   import sys
#   if sys.implementation.name == "micropython":
#       ...
#   if sys.implementation.version[0] >= 1:
#       ...
#   if sys.platform == "rp2":
#       ...


class _Implementation:
    """MicroPython's sys.implementation.

    Only `name` is carried. `version` is deliberately absent from the OBJECT:
    it has no runtime form (the compiler substitutes (1, 29, 0) at the
    `sys.implementation.version[i]` fold, never here), so a tuple stored on
    this class could only be a placeholder -- and a program that binds the
    object (`impl = sys.implementation`) would then read the fake. Refusing
    the attribute is the layer's contract. Upstream also exposes `_machine`,
    `_mpy`, `_build` and (thread-enabled builds) `_thread`; those are private,
    undocumented build-introspection fields no surveyed library reads, and are
    left out for the same reason the rest of `sys` is (see module docstring
    above).
    """

    def __init__(self):
        self.name = "micropython"


implementation = _Implementation()

# Placeholder; the compiler substitutes the real per-board string (see module
# docstring). Illustrative default matches the Pico, the most common board
# this layer builds for.
platform = "rp2"
