# MicroPython-style board constants for ATtiny13 bare chip (8-pin DIP)
# Also covers ATtiny13A (improved oscillator) -- same pinout.
# Very minimal: 1KB flash, 64B SRAM. No UART, no USI.

PB0 = "PB0"; PB1 = "PB1"; PB2 = "PB2"
PB3 = "PB3"; PB4 = "PB4"
PB5 = "PB5"   # RESET by default -- GPIO requires RSTDISBL fuse!

A0 = "PB5"; A1 = "PB2"; A2 = "PB4"; A3 = "PB3"

INT0 = "PB1"
