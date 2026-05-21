from pymcu_micropython.machine import (
    Pin, UART, ADC, PWM, SPI, I2C, _arduino_pin_name, time_pulse_us,
    Timer, WDT, freq, disable_irq, enable_irq, idle, lightsleep, deepsleep,
    IDLE, SLEEP, DEEPSLEEP,
    PWRON_RESET, HARD_RESET, WDT_RESET, DEEPSLEEP_RESET, SOFT_RESET,
    PIN_WAKE, RTC_WAKE, WLAN_WAKE,
    Signal, mem8, mem16,
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


def test_pin_init_mode():
    # Pin.init() is the standard MicroPython way to reinitialise a pin.
    pin = Pin(2, Pin.IN)
    pin.init(Pin.OUT)


def test_pin_call_read():
    # pin() is a fast shortcut for pin.value().
    pin = Pin(2, Pin.IN)
    v = pin(255)        # sentinel = read
    assert v == 0


def test_pin_call_write():
    pin = Pin(13, Pin.OUT)
    pin(1)
    pin(0)


# ── time_pulse_us ─────────────────────────────────────────────────────────  #

def test_time_pulse_us_returns_duration():
    # Mock _MockPin.pulse_in returns 50; time_pulse_us should relay that.
    pin = Pin(2, Pin.IN)
    dur = time_pulse_us(pin, 1, 200)
    assert dur == 50


def test_time_pulse_us_timeout_returns_minus_one():
    # When pulse_in returns 0 (timeout), time_pulse_us returns -1.
    import pymcu_micropython.machine as m_mod
    original = pin_obj = Pin(2, Pin.IN)
    pin_obj._pin.pulse_in = lambda state, timeout_us=1000: 0
    result = time_pulse_us(pin_obj, 1, 200)
    assert result == -1


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


# ── Module-level constants ────────────────────────────────────────────────  #

def test_sleep_mode_constants():
    assert IDLE      == 0
    assert SLEEP     == 1
    assert DEEPSLEEP == 2


def test_reset_cause_constants():
    assert PWRON_RESET     == 0
    assert HARD_RESET      == 1
    assert WDT_RESET       == 2
    assert DEEPSLEEP_RESET == 3
    assert SOFT_RESET      == 4


def test_wake_reason_constants():
    assert PIN_WAKE  == 0
    assert RTC_WAKE  == 1
    assert WLAN_WAKE == 2


# ── freq ─────────────────────────────────────────────────────────────────  #

def test_freq_returns_integer():
    f = freq()
    assert isinstance(f, int)


def test_freq_default_16mhz():
    # conftest sets chips.__FREQ__ = 16_000_000
    assert freq() == 16_000_000


# ── disable_irq / enable_irq ─────────────────────────────────────────────  #

def test_disable_irq_returns_nonzero():
    state = disable_irq()
    assert state != 0


def test_enable_irq_nonzero_state():
    # Should not raise; restores interrupts when state is truthy.
    state = disable_irq()
    enable_irq(state)


def test_enable_irq_zero_state():
    # Zero state leaves interrupts disabled (no call to enable_interrupts).
    enable_irq(0)  # must not raise


# ── idle / lightsleep / deepsleep ─────────────────────────────────────────  #

def test_idle_callable():
    idle()  # delegates to _sleep_idle mock; must not raise


def test_lightsleep_callable():
    lightsleep()  # delegates to _sleep_power_save mock


def test_deepsleep_callable():
    deepsleep()  # delegates to _sleep_power_down mock


# ── Timer constants ───────────────────────────────────────────────────────  #

def test_timer_mode_constants():
    assert Timer.ONE_SHOT == 0
    assert Timer.PERIODIC == 1


def test_timer_irq_constants():
    assert Timer.IRQ_OVF   == 1
    assert Timer.IRQ_COMPA == 2


# ── Timer instantiation and methods ──────────────────────────────────────  #

def test_timer_instantiation():
    t = Timer(0)
    assert t is not None


def test_timer_with_prescaler():
    t = Timer(1, 256)
    assert t is not None


def test_timer_start():
    t = Timer(0)
    t.start()  # must not raise


def test_timer_deinit():
    t = Timer(0)
    t.deinit()  # must not raise


def test_timer_init():
    t = Timer(0)
    t.init()  # stop + restart; must not raise


def test_timer_irq_registration():
    t = Timer(0)
    handler = lambda: None
    t.irq(handler)  # must not raise


def test_timer_irq_with_trigger():
    t = Timer(0)
    t.irq(lambda: None, Timer.IRQ_COMPA)


# ── WDT constants and instantiation ──────────────────────────────────────  #

def test_wdt_instantiation():
    wdt = WDT()
    assert wdt is not None


def test_wdt_with_timeout():
    wdt = WDT(timeout=2000)
    assert wdt is not None


def test_wdt_with_id_and_timeout():
    wdt = WDT(id=0, timeout=8000)
    assert wdt is not None


def test_wdt_feed():
    wdt = WDT(timeout=1000)
    wdt.feed()  # must not raise


def test_wdt_feed_multiple():
    wdt = WDT(timeout=500)
    for _ in range(5):
        wdt.feed()  # repeated feeds must not raise


# ── Signal ────────────────────────────────────────────────────────────────  #

def test_signal_instantiation_active_high():
    pin = Pin(13, Pin.OUT)
    sig = Signal(pin)
    assert sig is not None


def test_signal_instantiation_active_low():
    pin = Pin(13, Pin.OUT)
    sig = Signal(pin, invert=1)
    assert sig is not None


def test_signal_on_active_high():
    pin = Pin(13, Pin.OUT)
    sig = Signal(pin, invert=0)
    sig.on()
    assert pin.value() == 1


def test_signal_off_active_high():
    pin = Pin(13, Pin.OUT)
    sig = Signal(pin, invert=0)
    sig.on()
    sig.off()
    assert pin.value() == 0


def test_signal_on_active_low():
    pin = Pin(13, Pin.OUT)
    sig = Signal(pin, invert=1)
    sig.on()
    assert pin.value() == 0   # active-low: on() drives low


def test_signal_off_active_low():
    pin = Pin(13, Pin.OUT)
    sig = Signal(pin, invert=1)
    sig.on()
    sig.off()
    assert pin.value() == 1   # active-low: off() drives high


def test_signal_value_read_active_high():
    pin = Pin(13, Pin.OUT)
    sig = Signal(pin, invert=0)
    pin.high()
    assert sig.value() == 1
    pin.low()
    assert sig.value() == 0


def test_signal_value_read_active_low():
    pin = Pin(13, Pin.OUT)
    sig = Signal(pin, invert=1)
    pin.high()
    assert sig.value() == 0   # pin high -> signal inactive (0)
    pin.low()
    assert sig.value() == 1   # pin low  -> signal active (1)


def test_signal_value_write_active_high():
    pin = Pin(13, Pin.OUT)
    sig = Signal(pin, invert=0)
    sig.value(1)
    assert pin.value() == 1
    sig.value(0)
    assert pin.value() == 0


def test_signal_value_write_active_low():
    pin = Pin(13, Pin.OUT)
    sig = Signal(pin, invert=1)
    sig.value(1)            # logical 1 -> drive pin low
    assert pin.value() == 0
    sig.value(0)            # logical 0 -> drive pin high
    assert pin.value() == 1


# ── mem8 / mem16 ──────────────────────────────────────────────────────────  #

def test_mem8_exists():
    assert mem8 is not None


def test_mem8_has_subscript_interface():
    # ptr raises RuntimeError in CPython (compile-only semantics).
    # Verify the interface exists; actual reads/writes only work in firmware.
    assert hasattr(mem8, '__getitem__')
    assert hasattr(mem8, '__setitem__')


def test_mem16_exists():
    assert mem16 is not None


def test_mem16_has_subscript_interface():
    assert hasattr(mem16, '__getitem__')
    assert hasattr(mem16, '__setitem__')
