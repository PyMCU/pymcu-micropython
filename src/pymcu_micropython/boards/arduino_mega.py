# MicroPython-style board constants for Arduino Mega 2560 (ATmega2560 @ 16 MHz)
#
# The Mega has 54 digital + 16 analog pins. Since machine._arduino_pin_name
# only covers the Uno's D0-D13 mapping, pin constants here use port strings
# directly. Pass them to Pin() or HAL functions as-is.

# Digital pins D0-D13
D0  = "PE0"; D1  = "PE1"; D2  = "PE4"; D3  = "PE5"
D4  = "PG5"; D5  = "PE3"; D6  = "PH3"; D7  = "PH4"
D8  = "PH5"; D9  = "PH6"; D10 = "PB4"; D11 = "PB5"
D12 = "PB6"; D13 = "PB7"

# Digital pins D14-D21 (serial / I2C)
D14 = "PJ1"; D15 = "PJ0"; D16 = "PH1"; D17 = "PH0"
D18 = "PD3"; D19 = "PD2"; D20 = "PD1"; D21 = "PD0"

# Digital pins D22-D29 (Port A)
D22 = "PA0"; D23 = "PA1"; D24 = "PA2"; D25 = "PA3"
D26 = "PA4"; D27 = "PA5"; D28 = "PA6"; D29 = "PA7"

# Digital pins D30-D37 (Port C, reversed)
D30 = "PC7"; D31 = "PC6"; D32 = "PC5"; D33 = "PC4"
D34 = "PC3"; D35 = "PC2"; D36 = "PC1"; D37 = "PC0"

# Digital pins D38-D41
D38 = "PD7"; D39 = "PG2"; D40 = "PG1"; D41 = "PG0"

# Digital pins D42-D49 (Port L, reversed)
D42 = "PL7"; D43 = "PL6"; D44 = "PL5"; D45 = "PL4"
D46 = "PL3"; D47 = "PL2"; D48 = "PL1"; D49 = "PL0"

# Digital pins D50-D53 (SPI)
D50 = "PB3"; D51 = "PB2"; D52 = "PB1"; D53 = "PB0"

# Analog pins A0-A7 (Port F)
A0  = "PF0"; A1  = "PF1"; A2  = "PF2"; A3  = "PF3"
A4  = "PF4"; A5  = "PF5"; A6  = "PF6"; A7  = "PF7"

# Analog pins A8-A15 (Port K)
A8  = "PK0"; A9  = "PK1"; A10 = "PK2"; A11 = "PK3"
A12 = "PK4"; A13 = "PK5"; A14 = "PK6"; A15 = "PK7"

# Named aliases
LED         = "PB7"
LED_BUILTIN = "PB7"
TX   = "PE1"; RX   = "PE0"
TX1  = "PD3"; RX1  = "PD2"
TX2  = "PH1"; RX2  = "PH0"
TX3  = "PJ1"; RX3  = "PJ0"
SCL  = "PD0"; SDA  = "PD1"
SCK  = "PB1"; MOSI = "PB2"; MISO = "PB3"; SS = "PB0"
