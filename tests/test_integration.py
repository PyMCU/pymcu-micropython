"""
Integration tests for pymcu_micropython.

These tests exercise cross-module workflows: board pin constants flowing into
machine.* peripheral constructors, typical MicroPython usage patterns (blink,
ADC read, SPI transfer), and board_chips mappings.
"""
# ── Board imports ─────────────────────────────────────────────────────────── #

from pymcu_micropython.boards import arduino_uno, arduino_nano, arduino_mega, arduino_micro
from pymcu_micropython.boards import digispark
from pymcu_micropython.boards import attiny85, attiny84, attiny2313, attiny13
from pymcu_micropython.board_chips import BOARD_CHIPS

# ── Machine imports ───────────────────────────────────────────────────────── #

from pymcu_micropython.machine import (
    Pin, UART, ADC, PWM, SPI, I2C, _arduino_pin_name,
)


# ── board → machine.Pin (integer boards) ─────────────────────────────────── #

class TestBoardToPinInteger:
    """Arduino Uno/Nano expose integer D0-D13 that Pin() resolves via _arduino_pin_name."""

    def test_uno_led_output(self):
        led = Pin(arduino_uno.LED, Pin.OUT)
        assert led is not None

    def test_uno_d13_equals_led(self):
        assert arduino_uno.D13 == arduino_uno.LED

    def test_uno_blink_cycle(self):
        led = Pin(arduino_uno.D13, Pin.OUT)
        led.on()
        led.off()

    def test_uno_toggle(self):
        led = Pin(arduino_uno.D13, Pin.OUT)
        led.toggle()

    def test_uno_input_pin(self):
        btn = Pin(arduino_uno.D2, Pin.IN)
        v = btn.value()
        assert v == 0

    def test_uno_value_write(self):
        pin = Pin(arduino_uno.D5, Pin.OUT)
        pin.value(1)
        pin.value(0)

    def test_nano_led_output(self):
        led = Pin(arduino_nano.LED, Pin.OUT)
        assert led is not None

    def test_nano_d13_integer(self):
        assert arduino_nano.D13 == 13
        led = Pin(arduino_nano.D13, Pin.OUT)
        led.on()

    def test_uno_d1_d0_are_integers(self):
        # D1=TX, D0=RX on Uno -- just validate the integer type
        assert isinstance(arduino_uno.D1, int)
        assert isinstance(arduino_uno.D0, int)


# ── board → machine.Pin (port-string boards) ─────────────────────────────── #

class TestBoardToPinPortString:
    """Mega, Micro, ATtiny boards use port strings because _arduino_pin_name is Uno-only."""

    def test_mega_led_port_string(self):
        assert arduino_mega.LED == "PB7"
        led = Pin(arduino_mega.LED, Pin.OUT)
        assert led is not None

    def test_mega_d13_output(self):
        pin = Pin(arduino_mega.D13, Pin.OUT)
        pin.on()
        pin.off()

    def test_mega_d53_output(self):
        pin = Pin(arduino_mega.D53, Pin.OUT)
        assert pin is not None

    def test_micro_led(self):
        led = Pin(arduino_micro.LED, Pin.OUT)
        led.toggle()

    def test_digispark_led(self):
        led = Pin(digispark.LED, Pin.OUT)
        led.on()

    def test_digispark_p0_p1(self):
        p0 = Pin(digispark.P0, Pin.OUT)
        p1 = Pin(digispark.P1, Pin.OUT)
        p0.on()
        p1.off()

    def test_attiny85_pb1(self):
        pin = Pin(attiny85.PB1, Pin.OUT)
        assert pin is not None

    def test_attiny84_d0(self):
        pin = Pin(attiny84.D0, Pin.OUT)
        assert pin is not None

    def test_attiny2313_d0(self):
        pin = Pin(attiny2313.D0, Pin.IN)
        assert pin is not None

    def test_attiny13_pb0(self):
        pin = Pin(attiny13.PB0, Pin.OUT)
        assert pin is not None


# ── board → machine.ADC ───────────────────────────────────────────────────── #

class TestBoardToADC:
    def test_uno_a0_adc(self):
        adc = ADC(arduino_uno.A0)
        assert adc is not None

    def test_uno_a0_read_raises_in_cpython(self):
        # ADC.read() accesses hardware registers (ptr) that only work in
        # compiled code. In CPython the bit-check raises RuntimeError.
        import pytest
        adc = ADC(arduino_uno.A0)
        with pytest.raises(RuntimeError, match="compiled"):
            adc.read()

    def test_uno_a0_read_u16_raises_in_cpython(self):
        import pytest
        adc = ADC(arduino_uno.A0)
        with pytest.raises(RuntimeError, match="compiled"):
            adc.read_u16()

    def test_nano_a6_adc_only_pin(self):
        # ADC6/ADC7 are analog-only; still constructable
        adc = ADC(arduino_nano.A6)
        assert adc is not None

    def test_mega_a0_adc(self):
        adc = ADC(arduino_mega.A0)
        assert adc is not None

    def test_attiny85_a1(self):
        adc = ADC(attiny85.A1)
        assert adc is not None


# ── board → machine.PWM ───────────────────────────────────────────────────── #

class TestBoardToPWM:
    def test_uno_d6_pwm(self):
        pwm = PWM(arduino_uno.D6, freq=490, duty_u16=0)
        assert pwm is not None

    def test_uno_d6_set_duty(self):
        pwm = PWM(arduino_uno.D6)
        pwm.duty_u16(32768)

    def test_nano_d9_pwm(self):
        pwm = PWM(arduino_nano.D9)
        pwm.duty(128)

    def test_mega_d6_pwm(self):
        pwm = PWM(arduino_mega.D6)
        assert pwm is not None

    def test_digispark_p1_pwm(self):
        pwm = PWM(digispark.P1)
        assert pwm is not None

    def test_deinit(self):
        pwm = PWM(arduino_uno.D6)
        pwm.deinit()


# ── board → machine.UART ─────────────────────────────────────────────────── #

class TestBoardToUART:
    def test_uno_uart_default(self):
        uart = UART(0, baudrate=9600)
        assert uart is not None

    def test_uno_uart_write(self):
        uart = UART(0, baudrate=9600)
        uart.write(65)

    def test_uno_uart_read(self):
        uart = UART(0)
        b = uart.read()
        assert b == 0

    def test_uart_write_str(self):
        uart = UART(0)
        uart.write_str("hello")

    def test_uart_println(self):
        uart = UART(0)
        uart.println("test")


# ── board → machine.I2C ───────────────────────────────────────────────────── #

class TestBoardToI2C:
    def test_instantiation(self):
        i2c = I2C()
        assert i2c is not None

    def test_writeto_readfrom(self):
        i2c = I2C()
        i2c.writeto(0x68, 0x3B)
        val = i2c.readfrom(0x68)
        assert isinstance(val, int)


# ── board → machine.SPI ───────────────────────────────────────────────────── #

class TestBoardToSPI:
    def test_instantiation(self):
        spi = SPI()
        assert spi is not None

    def test_write(self):
        spi = SPI()
        spi.write(0xAB)

    def test_read(self):
        spi = SPI()
        val = spi.read()
        assert isinstance(val, int)

    def test_write_readinto(self):
        spi = SPI()
        val = spi.write_readinto(0xAB, 0)
        assert isinstance(val, int)


# ── board_chips ───────────────────────────────────────────────────────────── #

class TestBoardChips:
    def test_arduino_family(self):
        assert BOARD_CHIPS["arduino_uno"]   == "atmega328p"
        assert BOARD_CHIPS["arduino_nano"]  == "atmega328p"
        assert BOARD_CHIPS["arduino_mega"]  == "atmega2560"
        assert BOARD_CHIPS["arduino_micro"] == "atmega32u4"

    def test_digispark(self):
        assert BOARD_CHIPS["digispark"] == "attiny85"

    def test_attiny85_family(self):
        assert BOARD_CHIPS["attiny85"] == "attiny85"
        assert BOARD_CHIPS["attiny45"] == "attiny45"
        assert BOARD_CHIPS["attiny25"] == "attiny25"

    def test_attiny84_family(self):
        assert BOARD_CHIPS["attiny84"] == "attiny84"
        assert BOARD_CHIPS["attiny44"] == "attiny44"
        assert BOARD_CHIPS["attiny24"] == "attiny24"

    def test_attiny2313_family(self):
        assert BOARD_CHIPS["attiny2313"] == "attiny2313"
        assert BOARD_CHIPS["attiny4313"] == "attiny4313"

    def test_attiny13_family(self):
        assert BOARD_CHIPS["attiny13"] == "attiny13"
        assert BOARD_CHIPS["attiny13a"] == "attiny13a"

    def test_common_micropython_boards(self):
        assert BOARD_CHIPS["pyboard"]       == "stm32f405"
        assert BOARD_CHIPS["rp2040"]        == "rp2040"
        assert BOARD_CHIPS["esp32_generic"] == "esp32"

    def test_all_values_are_strings(self):
        for board_name, chip in BOARD_CHIPS.items():
            assert isinstance(chip, str), f"{board_name!r} chip must be a string"


# ── _arduino_pin_name integration with board constants ────────────────────── #

class TestArduinoPinNameWithBoardConstants:
    def test_d0_maps_correctly(self):
        assert _arduino_pin_name(arduino_uno.D0) == "PD0"

    def test_d7_maps_correctly(self):
        assert _arduino_pin_name(arduino_uno.D7) == "PD7"

    def test_d8_maps_to_portb(self):
        assert _arduino_pin_name(arduino_uno.D8) == "PB0"

    def test_d13_led_maps_correctly(self):
        assert _arduino_pin_name(arduino_uno.LED) == "PB5"

    def test_nano_identical_to_uno(self):
        for d in range(14):
            assert _arduino_pin_name(arduino_nano.__dict__.get(f"D{d}", d)) == \
                   _arduino_pin_name(arduino_uno.__dict__.get(f"D{d}", d))


# ── typical workflows ─────────────────────────────────────────────────────── #

class TestTypicalWorkflows:
    def test_blink_pattern(self):
        """Simulate 3 blink cycles."""
        led = Pin(arduino_uno.LED, Pin.OUT)
        for _ in range(3):
            led.on()
            led.off()

    def test_button_led_pattern(self):
        """Input controlling LED."""
        btn = Pin(arduino_uno.D2, Pin.IN)
        led = Pin(arduino_uno.D13, Pin.OUT)

        if btn.value() == 0:
            led.on()
        else:
            led.off()

    def test_adc_to_pwm_pattern(self):
        """Instantiate ADC and PWM; skip hardware read (ptr not available in CPython)."""
        import pytest
        adc = ADC(arduino_uno.A0)
        pwm = PWM(arduino_uno.D6)
        # Verify ADC.read() raises the expected CPython error
        with pytest.raises(RuntimeError):
            _ = adc.read()
        # PWM duty control works fine
        pwm.duty(128)
        pwm.deinit()

    def test_uart_echo_pattern(self):
        uart = UART(0, baudrate=9600)
        b = uart.read()
        uart.write(b)

    def test_mega_multi_serial_ports(self):
        """Mega has TX/TX1/TX2/TX3; just verify they are distinct port strings."""
        assert arduino_mega.TX  != arduino_mega.TX1
        assert arduino_mega.TX1 != arduino_mega.TX2
        assert arduino_mega.TX2 != arduino_mega.TX3

    def test_spi_exchange_pattern(self):
        spi = SPI()
        val = spi.write_readinto(0xFF, 0)
        assert isinstance(val, int)

    def test_i2c_sensor_pattern(self):
        i2c = I2C()
        i2c.writeto(0x76, 0xD0)   # read chip-id register
        chip_id = i2c.readfrom(0x76)
        assert isinstance(chip_id, int)
