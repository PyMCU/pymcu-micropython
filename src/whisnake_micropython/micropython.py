# MicroPython-compatible micropython module for Whisnake
#
# micropython.const(N) is a MicroPython idiom to hint that an integer
# expression is a compile-time constant. In Whisnake, all integer literals
# and const[T]-annotated variables are already compile-time constants, so
# const() is treated as an identity function.
#
# native and viper decorators are silently ignored (all Whisnake functions
# targeting a flat ISA are already "native" -- no interpreter overhead).
#
# Usage:
#   import micropython
#   BAUD = micropython.const(9600)    # => integer literal 9600
#
#   @micropython.native   # silently ignored
#   def fast_func():
#       ...

from whisnake.types import inline


@inline
def const(value):
    # Identity -- the compiler sees the literal directly.
    return value


def native(f):
    # Silently ignored: Whisnake emits native machine code for all functions.
    return f


def viper(f):
    # Silently ignored: use @inline for zero-cost inlining in Whisnake.
    return f
