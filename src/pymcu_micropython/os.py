# MicroPython-compatible os module for PyMCU
#
# Only `uname()` is provided, because that is the whole of `os` the MicroPython
# library ecosystem reaches for at branch time to tell ports apart (PyMCU
# docs/rfcs/0007; the survey that motivated this module found adafruit_dht.py
# reading os.uname() exactly this way on the CircuitPython side).
#
# Everything else MicroPython's os documents -- chdir, getcwd, listdir, mkdir,
# remove, rename, rmdir, stat, statvfs, sync, urandom, dupterm, VfsFat/VfsLfs2
# -- needs a filesystem this target does not have, and is not here: adding a
# stub that returns "" or [] for a directory listing would be a fake value
# standing in for a real refusal.
#
# `getenv()` is not part of MicroPython's os (that is a CircuitPython-only
# addition, over /settings.toml); it is intentionally absent here rather than
# added to look symmetric with a CircuitPython flavor.
#
# COMPILE-TIME CONSTANT. `uname()` (and reading a field off its result, or
# asking whether a string is `in`/`not in` it) is resolved and substituted by
# the compiler at the point it is read, exactly the way `__CHIP__.arch` is (see
# pymcu.chips). The values below are placeholders for IDEs and for
# `import pymcu_micropython.os` under plain CPython (this layer's own parity
# suite) -- a compiled program never actually runs this function's body. The
# real per-board table is in docs/rfcs/0007 in the PyMCU repo:
#
#   sysname / nodename are MicroPython's own port short name where one exists
#   ("rp2" on the Pico and the Pico 2, the SAME string MicroPython's os.uname()
#   uses for both -- unlike CircuitPython, whose os.uname().sysname is the MCU
#   name, a different field entirely) and the plain chip name where no
#   upstream port exists (every AVR part, CH32V003).
#
#   release is "1.29.0" on every board (the MicroPython API surface this
#   layer's parity suite is pinned against, see sys.py); version is a fixed,
#   honestly-labelled PyMCU build stamp, never a fabricated git tag and date
#   (no surveyed library reads it); machine is "<board display name> with
#   <MCU name>", matching upstream's own `"<BOARD> with <MCU>"` construction
#   (note: machine's second half is the MCU name, e.g. "RP2040", even though
#   sysname on this port is "rp2" -- upstream's own os.uname() uses both
#   concepts in the same tuple).
#
# Usage:
#   from os import uname
#   if uname().sysname == "rp2":
#       ...

# Underscore-aliased: upstream os has no `namedtuple` member, and a visible
# `os.namedtuple` would be a name that exists here but not on a board.
from collections import namedtuple as _namedtuple
from pymcu.types import inline

_Uname = _namedtuple("_Uname", ["sysname", "nodename", "release", "version", "machine"])


# @inline like pymcu.os.stat/os.listdir: the body expands only where it is
# called, which is what lets the `raise` name the caller's line. A plain def
# would be lowered as soon as the module is imported and refuse every program
# that touches `os` at all.
@inline
def uname():
    """Returns a named tuple of system information. COMPILE-TIME CONSTANT: the
    compiler substitutes the real per-board values at every read site;
    see docs/rfcs/0007 in the PyMCU repo.
    """
    # The compiler folds `uname().<field>` and `"x" in uname()` before this body
    # is ever reached. A BARE `u = uname()` would need a runtime tuple object to
    # hold the answer, and there is none -- the same refusal pymcu.os.stat and
    # os.listdir make for the same reason. Returning the placeholder fields
    # here instead would answer every field read with "", silently. The import
    # is function-local so `CompileError` does not leak into this module's
    # public surface (upstream os has no such member).
    from pymcu.exceptions import CompileError
    raise CompileError(
        "os.uname() has no runtime object: read its fields directly "
        "(uname().sysname / .machine) or test membership "
        "('x' in uname()) -- the compiler answers both"
    )
