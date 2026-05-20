from pymcu_micropython.boards import arduino_uno
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


# ── board_chips ──────────────────────────────────────────────────────────  #

def test_board_chips_is_dict():
    assert isinstance(BOARD_CHIPS, dict)


def test_board_chips_arduino_uno():
    assert BOARD_CHIPS["arduino_uno"] == "atmega328p"


def test_board_chips_known_boards():
    assert BOARD_CHIPS["pyboard"]       == "stm32f405"
    assert BOARD_CHIPS["rp2040"]        == "rp2040"
    assert BOARD_CHIPS["esp32_generic"] == "esp32"
