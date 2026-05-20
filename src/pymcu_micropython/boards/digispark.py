# MicroPython-style board constants for Digispark (ATtiny85 @ 16.5 MHz USB)
# Port strings used directly (no integer mapping for ATtiny in machine.py).

P0 = "PB0"; P1 = "PB1"; P2 = "PB2"
P3 = "PB3"; P4 = "PB4"
P5 = "PB5"   # RESET by default -- GPIO requires RSTDISBL fuse!

A0 = "PB5"; A1 = "PB2"; A2 = "PB4"; A3 = "PB3"

LED         = "PB1"
LED_BUILTIN = "PB1"
SCK  = "PB2"; MOSI = "PB0"; MISO = "PB1"
SCL  = "PB2"; SDA  = "PB0"
