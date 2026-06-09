# 16x2 HD44780 LCD over I2C (PCF8574 backpack) -- MicroPython style.
#
# API:
#   lcd = LcdI2c(I2C(), 0x27)
#   lcd.init()
#   lcd.move_to(col, row)
#   lcd.puts("text")
#   lcd.putchar(code)
#   lcd.command(cmd)
#
# Hardware: the common "LCD1602 I2C" module (PCF8574 I/O expander driving an
# HD44780 in 4-bit mode). Wiring on Arduino Uno: SDA=A4, SCL=A5, VCC=5V, GND.
#
# PCF8574 -> HD44780 bit map (4-bit mode):
#   P0=RS  P1=RW  P2=EN  P3=Backlight  P4..P7 = D4..D7
from pymcu.types import uint8, inline, const
from machine import I2C
from utime import sleep_ms, sleep_us

_BL = 0x08          # backlight on
_EN = 0x04          # enable strobe
_RS = 0x01          # register select (1 = data, 0 = command)


class LcdI2c:
    @inline
    def __init__(self, i2c: I2C, addr: uint8 = 0x27):
        self._i2c = i2c
        self._addr = addr

    @inline
    def _nibble(self, nib: uint8, rs: uint8):
        # Present the high nibble + control bits, pulse EN high then low to latch.
        base: uint8 = (nib & 0xF0) | rs | _BL
        self._i2c.writeto(self._addr, base | _EN)
        self._i2c.writeto(self._addr, base)

    @inline
    def _byte(self, val: uint8, rs: uint8):
        self._nibble(val & 0xF0, rs)
        self._nibble((val << 4) & 0xF0, rs)

    @inline
    def command(self, c: uint8):
        self._byte(c, 0)

    @inline
    def putchar(self, c: uint8):
        self._byte(c, _RS)

    @inline
    def init(self):
        sleep_ms(50)
        # 4-bit init dance (datasheet)
        self._nibble(0x30, 0)
        sleep_ms(5)
        self._nibble(0x30, 0)
        sleep_us(150)
        self._nibble(0x30, 0)
        self._nibble(0x20, 0)       # set 4-bit mode
        self.command(0x28)          # function set: 4-bit, 2 lines, 5x8 font
        self.command(0x0C)          # display on, cursor off, blink off
        self.command(0x06)          # entry mode: increment, no shift
        self.command(0x01)          # clear display
        sleep_ms(2)

    @inline
    def move_to(self, col: uint8, row: uint8):
        base: uint8 = 0x00
        if row == 1:
            base = 0x40
        self.command(0x80 | (base + col))

    @inline
    def puts(self, s: const[str]):
        for c in s:
            self.putchar(c)
