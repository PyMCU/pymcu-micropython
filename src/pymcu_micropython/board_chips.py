# Board -> chip mapping for boards known to the MicroPython flavor.
# The PyMCU build driver merges this into its own BOARD_CHIPS dict at build time.
# Extension entries take precedence over the built-in driver mapping.

BOARD_CHIPS: dict = {
    # Common MicroPython boards
    "pyboard":          "stm32f405",
    "pyboard_v11":      "stm32f405",
    "rp2040":           "rp2040",
    "esp32_generic":    "esp32",
    "esp8266_generic":  "esp8266",
    # Arduino / AVR
    "arduino_uno":      "atmega328p",
    "arduino_nano":     "atmega328p",
    "arduino_mega":     "atmega2560",
    "arduino_micro":    "atmega32u4",
    # ATtiny named dev boards
    "digispark":        "attiny85",
    "adafruit_trinket": "attiny85",
    # ATtiny bare chips -- 8-pin
    "attiny85":  "attiny85",
    "attiny45":  "attiny45",
    "attiny25":  "attiny25",
    "attiny13":  "attiny13",
    "attiny13a": "attiny13a",
    # ATtiny bare chips -- 14-pin
    "attiny84": "attiny84",
    "attiny44": "attiny44",
    "attiny24": "attiny24",
    # ATtiny bare chips -- 20-pin
    "attiny2313": "attiny2313",
    "attiny4313": "attiny4313",
}
