# MicroPython-style board constants for Arduino Micro (ATmega32U4 @ 16 MHz)
#
# Port strings are used directly since machine._arduino_pin_name covers Uno only.

D0  = "PD2"; D1  = "PD3"; D2  = "PD1"; D3  = "PD0"
D4  = "PD4"; D5  = "PC6"; D6  = "PD7"; D7  = "PE6"
D8  = "PB4"; D9  = "PB5"; D10 = "PB6"; D11 = "PB7"
D12 = "PD6"; D13 = "PC7"

A0 = "PF7"; A1 = "PF6"; A2 = "PF5"; A3 = "PF4"
A4 = "PF1"; A5 = "PF0"

LED         = "PC7"
LED_BUILTIN = "PC7"
TX   = "PD3"; RX  = "PD2"
SCL  = "PD0"; SDA = "PD1"
SCK  = "PB1"; MOSI = "PB2"; MISO = "PB3"; SS = "PB0"
