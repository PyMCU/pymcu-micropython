# 16x2 I2C LCD demo (MicroPython style) on Arduino Uno.
#
#   from machine import I2C
#   from lcd_i2c import LcdI2c
#   lcd = LcdI2c(I2C(), 0x27)
#
# Wiring: SDA=A4 (PC4), SCL=A5 (PC5), VCC=5V, GND. Backpack address usually 0x27 or 0x3F.
from machine import I2C
from utime import sleep_ms
from lcd_i2c import LcdI2c

i2c = I2C()
lcd = LcdI2c(i2c, 0x27)
lcd.init()

while True:
    lcd.move_to(0, 0)
    lcd.puts("PyMCU I2C LCD")
    lcd.move_to(0, 1)
    lcd.puts("Hello, world!")
    sleep_ms(1000)
