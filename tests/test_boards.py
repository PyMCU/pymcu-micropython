from pymcu_micropython.boards import (
    arduino_uno, arduino_nano, arduino_mega, arduino_micro,
    digispark, attiny85, attiny45, attiny25, attiny84, attiny44, attiny24,
    attiny2313, attiny4313, attiny13, attiny13a,
)
from pymcu_micropython.board_chips import BOARD_CHIPS


# ── Arduino Uno digital pins (integer numbers) ────────────────────────────  #

def test_arduino_uno_digital_pins():
    assert arduino_uno.D0  == 0
    assert arduino_uno.D1  == 1
    assert arduino_uno.D2  == 2
    assert arduino_uno.D7  == 7
    assert arduino_uno.D8  == 8
    assert arduino_uno.D13 == 13


def test_arduino_uno_analog_pins():
    # MicroPython analog pins keep their port-string form
    assert arduino_uno.A0 == "PC0"
    assert arduino_uno.A1 == "PC1"
    assert arduino_uno.A4 == "PC4"
    assert arduino_uno.A5 == "PC5"


def test_arduino_uno_led():
    assert arduino_uno.LED         == 13
    assert arduino_uno.LED_BUILTIN == 13


# ── Arduino Nano ─────────────────────────────────────────────────────────  #

def test_arduino_nano_digital_pins():
    assert arduino_nano.D0  == 0
    assert arduino_nano.D13 == 13


def test_arduino_nano_analog_pins():
    assert arduino_nano.A0 == "PC0"
    assert arduino_nano.A5 == "PC5"
    assert arduino_nano.A6 == "ADC6"
    assert arduino_nano.A7 == "ADC7"


def test_arduino_nano_led():
    assert arduino_nano.LED         == 13
    assert arduino_nano.LED_BUILTIN == 13


# ── Arduino Mega ──────────────────────────────────────────────────────────  #

def test_arduino_mega_digital_pins():
    assert arduino_mega.D0  == "PE0"
    assert arduino_mega.D13 == "PB7"
    assert arduino_mega.D53 == "PB0"


def test_arduino_mega_analog_pins():
    assert arduino_mega.A0  == "PF0"
    assert arduino_mega.A15 == "PK7"


def test_arduino_mega_named_pins():
    assert arduino_mega.LED         == "PB7"
    assert arduino_mega.LED_BUILTIN == "PB7"
    assert arduino_mega.TX  == "PE1"
    assert arduino_mega.SCL == "PD0"


# ── Arduino Micro ─────────────────────────────────────────────────────────  #

def test_arduino_micro_digital_pins():
    assert arduino_micro.D0  == "PD2"
    assert arduino_micro.D13 == "PC7"


def test_arduino_micro_named_pins():
    assert arduino_micro.LED         == "PC7"
    assert arduino_micro.LED_BUILTIN == "PC7"
    assert arduino_micro.TX  == "PD3"
    assert arduino_micro.RX  == "PD2"


# ── Digispark ─────────────────────────────────────────────────────────────  #

def test_digispark_pins():
    assert digispark.P0 == "PB0"
    assert digispark.P1 == "PB1"
    assert digispark.P5 == "PB5"
    assert digispark.LED         == "PB1"
    assert digispark.LED_BUILTIN == "PB1"


# ── ATtiny85 family ───────────────────────────────────────────────────────  #

def test_attiny85_pins():
    assert attiny85.PB0 == "PB0"
    assert attiny85.PB5 == "PB5"
    assert attiny85.A1  == "PB2"
    assert attiny85.SCL == "PB2"


def test_attiny45_pins():
    assert attiny45.PB0 == "PB0"
    assert attiny45.A1  == "PB2"


def test_attiny25_pins():
    assert attiny25.PB0 == "PB0"
    assert attiny25.A1  == "PB2"


# ── ATtiny84 family ───────────────────────────────────────────────────────  #

def test_attiny84_pins():
    assert attiny84.D0  == "PA0"
    assert attiny84.D8  == "PB0"
    assert attiny84.D10 == "PB2"
    assert attiny84.A7  == "PA7"


def test_attiny44_pins():
    assert attiny44.D0 == "PA0"
    assert attiny44.D8 == "PB0"


def test_attiny24_pins():
    assert attiny24.D0 == "PA0"
    assert attiny24.D8 == "PB0"


# ── ATtiny2313 family ─────────────────────────────────────────────────────  #

def test_attiny2313_pins():
    assert attiny2313.D0  == "PD0"
    assert attiny2313.D14 == "PB7"
    assert attiny2313.TX  == "PD1"
    assert attiny2313.RX  == "PD0"


def test_attiny4313_pins():
    assert attiny4313.D0  == "PD0"
    assert attiny4313.D14 == "PB7"


# ── ATtiny13 family ───────────────────────────────────────────────────────  #

def test_attiny13_pins():
    assert attiny13.PB0  == "PB0"
    assert attiny13.PB5  == "PB5"
    assert attiny13.INT0 == "PB1"


def test_attiny13a_pins():
    assert attiny13a.PB0  == "PB0"
    assert attiny13a.INT0 == "PB1"


# ── board_chips ──────────────────────────────────────────────────────────  #

def test_board_chips_is_dict():
    assert isinstance(BOARD_CHIPS, dict)


def test_board_chips_arduino_uno():
    assert BOARD_CHIPS["arduino_uno"] == "atmega328p"


def test_board_chips_known_boards():
    assert BOARD_CHIPS["pyboard"]       == "stm32f405"
    assert BOARD_CHIPS["rp2040"]        == "rp2040"
    assert BOARD_CHIPS["esp32_generic"] == "esp32"


def test_board_chips_arduino_family():
    assert BOARD_CHIPS["arduino_nano"]  == "atmega328p"
    assert BOARD_CHIPS["arduino_mega"]  == "atmega2560"
    assert BOARD_CHIPS["arduino_micro"] == "atmega32u4"


def test_board_chips_attiny_named():
    assert BOARD_CHIPS["digispark"]        == "attiny85"
    assert BOARD_CHIPS["adafruit_trinket"] == "attiny85"


def test_board_chips_attiny_bare():
    assert BOARD_CHIPS["attiny85"]   == "attiny85"
    assert BOARD_CHIPS["attiny84"]   == "attiny84"
    assert BOARD_CHIPS["attiny2313"] == "attiny2313"
    assert BOARD_CHIPS["attiny13"]   == "attiny13"
