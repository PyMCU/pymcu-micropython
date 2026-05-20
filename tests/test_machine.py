from pymcu_micropython.machine import (
    Pin, UART, ADC, PWM, SPI, I2C, _arduino_pin_name,
)


# ── _arduino_pin_name ─────────────────────────────────────────────────────  #

def test_arduino_pin_name_portd():
    assert _arduino_pin_name(0) == "PD0"
    assert _arduino_pin_name(1) == "PD1"
    assert _arduino_pin_name(7) == "PD7"


def test_arduino_pin_name_portb():
    assert _arduino_pin_name(8)  == "PB0"
    assert _arduino_pin_name(13) == "PB5"


def test_arduino_pin_name_default():
    # Out-of-range falls back to PB5 (LED pin)
    assert _arduino_pin_name(99) == "PB5"


# ── Pin constants ─────────────────────────────────────────────────────────  #

def test_pin_mode_constants():
    assert Pin.IN  == 1
    assert Pin.OUT == 0


def test_pin_pull_constants():
    assert Pin.PULL_UP   == 1
    assert Pin.PULL_DOWN == 2


def test_pin_irq_constants():
    assert Pin.IRQ_FALLING == 1
    assert Pin.IRQ_RISING  == 2


# ── Pin instantiation and methods ─────────────────────────────────────────  #

def test_pin_output_instantiation():
    led = Pin(13, Pin.OUT)
    assert led is not None


def test_pin_input_instantiation():
    btn = Pin(2, Pin.IN)
    assert btn is not None


def test_pin_high_low():
    pin = Pin(13, Pin.OUT)
    pin.high()
    pin.low()


def test_pin_on_off():
    pin = Pin(13, Pin.OUT)
    pin.on()
    pin.off()


def test_pin_toggle():
    pin = Pin(13, Pin.OUT)
    pin.toggle()


def test_pin_value_read():
    pin = Pin(2, Pin.IN)
    v = pin.value()
    assert v == 0


def test_pin_value_write():
    pin = Pin(13, Pin.OUT)
    pin.value(1)
    pin.value(0)


def test_pin_irq():
    pin = Pin(2, Pin.IN)
    pin.irq(Pin.IRQ_FALLING)


def test_pin_mode_read():
    pin = Pin(13, Pin.OUT)
    m = pin.mode()
    assert m == Pin.OUT


def test_pin_mode_write():
    pin = Pin(2, Pin.IN)
    pin.mode(Pin.OUT)


# ── UART ──────────────────────────────────────────────────────────────────  #

def test_uart_instantiation():
    uart = UART(0, 9600)
    assert uart is not None


def test_uart_write():
    uart = UART(0, 9600)
    uart.write(65)


def test_uart_read():
    uart = UART(0)
    b = uart.read()
    assert b == 0


def test_uart_write_str():
    uart = UART(0, 9600)
    uart.write_str("hello")


def test_uart_println():
    uart = UART(0, 9600)
    uart.println("test")


# ── ADC ───────────────────────────────────────────────────────────────────  #

def test_adc_instantiation():
    adc = ADC("A0")
    assert adc is not None


def test_adc_has_read_methods():
    adc = ADC("A0")
    assert callable(adc.read)
    assert callable(adc.read_u16)


# ── PWM ───────────────────────────────────────────────────────────────────  #

def test_pwm_instantiation():
    pwm = PWM(Pin(6, Pin.OUT), freq=1000, duty_u16=0)
    assert pwm is not None


def test_pwm_init_deinit():
    pwm = PWM(Pin(6, Pin.OUT))
    pwm.init()
    pwm.deinit()


def test_pwm_duty_u16():
    pwm = PWM(Pin(6, Pin.OUT))
    pwm.duty_u16(32768)


def test_pwm_duty():
    pwm = PWM(Pin(6, Pin.OUT))
    pwm.duty(128)


# ── SPI ───────────────────────────────────────────────────────────────────  #

def test_spi_instantiation():
    spi = SPI()
    assert spi is not None


def test_spi_write():
    spi = SPI()
    spi.write(0xAB)


def test_spi_read():
    spi = SPI()
    val = spi.read()
    assert val == 0


def test_spi_write_readinto():
    spi = SPI()
    val = spi.write_readinto(0xAB, 0)
    assert val == 0


# ── I2C ───────────────────────────────────────────────────────────────────  #

def test_i2c_instantiation():
    i2c = I2C()
    assert i2c is not None


def test_i2c_writeto():
    i2c = I2C()
    i2c.writeto(0x68, 0x00)


def test_i2c_readfrom():
    i2c = I2C()
    val = i2c.readfrom(0x68)
    assert val == 0


def test_i2c_scan_returns_int():
    i2c = I2C()
    count = i2c.scan()
    assert isinstance(count, int)
    assert count == 0  # mock always returns 0 from ping
