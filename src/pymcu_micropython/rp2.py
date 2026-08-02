# -----------------------------------------------------------------------------
# PyMCU MicroPython compatibility -- rp2 (PIO)
# SPDX-License-Identifier: MIT
# -----------------------------------------------------------------------------
# The PyMCU frontend intercepts the @rp2.asm_pio decorator (at parse time) and
# the rp2.StateMachine(...) construction (in IR generation); these stubs exist
# only so the names resolve and the source parses like real MicroPython.


class PIO:
    IN_LOW = 0
    IN_HIGH = 1
    OUT_LOW = 2
    OUT_HIGH = 3
    SHIFT_LEFT = 0
    SHIFT_RIGHT = 1
    JOIN_NONE = 0
    JOIN_TX = 1
    JOIN_RX = 2


def asm_pio(set_init: int = 0):
    # Never invoked: @rp2.asm_pio is handled by the PyMCU parser.
    pass


class StateMachine:
    def __init__(self, sm_id: int = 0):
        # Never invoked: StateMachine(...) is intercepted by the IR generator.
        pass
