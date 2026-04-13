# MicroPython-compatible micropython module for Whipsnake
#
# micropython.const(N) is a MicroPython idiom to hint that an integer
# expression is a compile-time constant. In Whipsnake, all integer literals
# and const[T]-annotated variables are already compile-time constants, so
# const() is treated as an identity function.
#
# native and viper decorators are silently ignored (all Whipsnake functions
# targeting a flat ISA are already "native" -- no interpreter overhead).
#
# Usage:
#   import micropython
#   BAUD = micropython.const(9600)    # => integer literal 9600
#
#   @micropython.native   # silently ignored
#   def fast_func():
#       ...

from pymcu.types import inline


@inline
def const(value):
    # Identity -- the compiler sees the literal directly.
    return value


def native(f):
    # Silently ignored: Whipsnake emits native machine code for all functions.
    return f


def viper(f):
    # Silently ignored: use @inline for zero-cost inlining in Whipsnake.
    return f
