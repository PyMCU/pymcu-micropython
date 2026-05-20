# MicroPython-style board constants for ATtiny85 bare chip (8-pin DIP)
# Also covers ATtiny45 (4KB flash) and ATtiny25 (2KB flash) -- same pinout.

PB0 = "PB0"; PB1 = "PB1"; PB2 = "PB2"
PB3 = "PB3"; PB4 = "PB4"
PB5 = "PB5"   # RESET by default -- GPIO requires RSTDISBL fuse!

A0 = "PB5"; A1 = "PB2"; A2 = "PB4"; A3 = "PB3"

SCK  = "PB2"; MOSI = "PB0"; MISO = "PB1"
SCL  = "PB2"; SDA  = "PB0"; INT0 = "PB2"
