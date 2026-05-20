# MicroPython-style board constants for Arduino Nano (ATmega328P @ 16 MHz)
#
# Identical pinout to Arduino Uno. Integer pin numbers match silk-screen.
# MicroPython uses integer pin numbers resolved to port strings by the compiler.

# Digital pins (same numbering as Arduino silk-screen)
D0  = 0     # PD0 / RX
D1  = 1     # PD1 / TX
D2  = 2     # PD2 / INT0
D3  = 3     # PD3 / INT1 / OC2B
D4  = 4     # PD4
D5  = 5     # PD5 / OC0B
D6  = 6     # PD6 / OC0A
D7  = 7     # PD7
D8  = 8     # PB0
D9  = 9     # PB1 / OC1A
D10 = 10    # PB2 / SS / OC1B
D11 = 11    # PB3 / MOSI / OC2A
D12 = 12    # PB4 / MISO
D13 = 13    # PB5 / SCK / LED

# Analog pins (port-string form; no standard integer offset on Nano)
A0 = "PC0"
A1 = "PC1"
A2 = "PC2"
A3 = "PC3"
A4 = "PC4"   # SDA
A5 = "PC5"   # SCL
A6 = "ADC6"  # ADC-only (no GPIO; not connected to a port pin)
A7 = "ADC7"  # ADC-only (no GPIO; not connected to a port pin)

# Named aliases
LED         = 13
LED_BUILTIN = 13
TX   = 1
RX   = 0
