# DHT11 Sensor -- MicroPython style on Arduino Uno
#
# Demonstrates:
#   machine.Pin  -- integer pin numbers (D2 = PD2 sensor, D13 = PB5 LED)
#   print()       -- UART 0 auto-initialized at 115200 baud by pymcu build
#   utime        -- sleep_ms() between measurements
#   local driver -- dht11.DHT11 reads temperature and humidity
#
# MicroPython equivalent (runs unmodified on any MicroPython board with DHT):
#   from machine import Pin
#   from utime import sleep_ms
#   from dht import DHT11
#   sensor = DHT11(Pin(2, Pin.IN))
#
# Wiring:
#   DHT11 DATA -> D2  (4.7 kohm pull-up to +5 V recommended)
#   DHT11 VCC  -> +5 V
#   DHT11 GND  -> GND
#   LED:    built-in on D13 (no wiring needed)
#
# UART output (115200 baud, auto-initialized by pymcu build):
#   Boot:  "DHT11 ready"
#   OK:    "H: XX  T: XX"
#   Error: "read error"

from machine import Pin
from utime import sleep_ms
from dht import DHT11


led    = Pin(13, Pin.OUT)
sensor = DHT11(Pin(2, Pin.IN))

print("DHT11 ready")

while True:
    sensor.measure()

    if sensor.failed:
        print("read error")
        led.low()
    else:
        print("H: ", sensor.humidity(), "  T: ", sensor.temperature(), sep="")
        led.high()
        sleep_ms(100)
        led.low()

    sleep_ms(2000)
