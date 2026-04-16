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
    # Arduino / AVR (shared with CP mapping)
    "arduino_uno":      "atmega328p",
}
