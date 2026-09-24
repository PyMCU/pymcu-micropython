import pytest
from pymcu.exceptions import CompileError

from pymcu_micropython.machine import (
    Pin, UART, ADC, PWM, SPI, SoftSPI, I2C, SoftI2C, time_pulse_us,
    Timer, WDT, freq, disable_irq, enable_irq, idle, lightsleep, deepsleep,
    PWRON_RESET, WDT_RESET, reset_cause,
    Signal, mem8, mem16, mem32,
)


# ── board pin numbers ─────────────────────────────────────────────────────  #
# Integer pins are resolved by the HAL's board_pin_name (stubbed in conftest with the
# Uno's table); the layer keeps no table of its own since 33374b0.

def test_pin_number_portd():
    assert Pin(0)._name == "PD0"
    assert Pin(1)._name == "PD1"
    assert Pin(7)._name == "PD7"


def test_pin_number_portb():
    assert Pin(8)._name == "PB0"
    assert Pin(13)._name == "PB5"


def test_pin_number_out_of_range_is_refused():
    # Out of range is refused, not quietly mapped to the LED: Pin(25) used
    # to build and drive PB5.
    with pytest.raises(CompileError):
        Pin(99)


# ── Pin constants ─────────────────────────────────────────────────────────  #

def test_pin_mode_constants():
    assert Pin.IN         == 0
    assert Pin.OUT        == 1
    assert Pin.OPEN_DRAIN == 2


def test_pin_pull_constants():
    assert Pin.PULL_UP   == 1
    assert Pin.PULL_DOWN == 2


def test_pin_irq_constants():
    assert Pin.IRQ_FALLING == 4
    assert Pin.IRQ_RISING  == 8


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


def test_pin_irq_with_handler():
    pin = Pin(2, Pin.IN)
    handler = lambda: None
    pin.irq(handler=handler, trigger=Pin.IRQ_FALLING)


def test_pin_irq_handler_only():
    # handler as positional argument (first param), trigger defaults to IRQ_FALLING
    pin = Pin(2, Pin.IN)
    pin.irq(lambda: None)


def test_pin_irq_rising_with_handler():
    pin = Pin(2, Pin.IN)
    pin.irq(lambda: None, Pin.IRQ_RISING)


def test_pin_mode_and_pull_names_are_absent():
    # Pin.mode() / Pin.pull() / Pin.drive() are declared by the shared stub but
    # the rp2 port never defines them -- re-initialisation goes through
    # Pin.init(mode=..., pull=...) there, so the names stay absent here.
    pin = Pin(13, Pin.OUT)
    for name in ("mode", "pull", "drive"):
        assert not hasattr(pin, name), name


def test_pin_init_mode():
    # Pin.init() is the standard MicroPython way to reinitialise a pin.
    pin = Pin(2, Pin.IN)
    pin.init(Pin.OUT)


def test_pin_call_read():
    # pin() is a fast shortcut for pin.value().
    pin = Pin(2, Pin.IN)
    v = pin()
    assert v == 0


def test_pin_call_write():
    pin = Pin(13, Pin.OUT)
    pin(1)
    pin(0)


def test_pin_call_write_255_is_not_a_read():
    # Regression for the value()/mode()/Signal.value() sentinel bug (255
    # doubled as both "read" and the largest real uint8 value, so
    # pin(255)/pin.value(255) silently read instead of driving the pin
    # high): two real overloads means there is no longer a value that
    # collides with "no argument".
    pin = Pin(13, Pin.OUT)
    v = pin(255)
    assert v is None
    v = pin.value(255)
    assert v is None


def test_pin_irq_upstream_kwargs():
    # Upstream signature: irq(handler, trigger=FALLING|RISING, *, priority=1,
    # wake=None, hard=False). The keywords are accepted at their defaults;
    # a non-default priority or a wake source is refused by name.
    pin = Pin(2, Pin.IN)
    pin.irq(lambda: None, Pin.IRQ_FALLING, priority=1, hard=True)
    with pytest.raises(CompileError):
        pin.irq(lambda: None, Pin.IRQ_FALLING, priority=2)
    with pytest.raises(CompileError):
        pin.irq(lambda: None, Pin.IRQ_FALLING, wake=70)


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


def test_uart_extension_names_are_absent():
    # irq / write_str / println / print_byte are not upstream rp2 UART members
    # (measured on MicroPython 1.21): irq is an esp32-port stub declaration and
    # the rest were PyMCU conveniences. println("x") is uart.write("x\n").
    uart = UART(0, 9600)
    for name in ("irq", "write_str", "println", "print_byte"):
        assert not hasattr(uart, name), name


def test_uart_write_string_form():
    # write() takes a str (a buffer under MicroPython) -- the upstream
    # equivalent of the removed println.
    uart = UART(0, 9600)
    uart.write("test\n")


# ── ADC ───────────────────────────────────────────────────────────────────  #

def test_adc_instantiation():
    adc = ADC(0)
    assert adc is not None


def test_adc_from_adc_preserves_the_underlying_channel():
    adc = ADC(0)
    assert ADC(adc)._adc is adc._adc


def test_adc_has_read_methods():
    adc = ADC(0)
    # Upstream rp2 exposes read_u16() only; read() is an esp32-port name the
    # stub carries over.
    assert not hasattr(adc, "read")
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


def test_pwm_duty_name_is_absent():
    # PWM.duty() is the esp32 legacy 0..1023 spelling; upstream rp2 exposes
    # duty_u16()/duty_ns() only (measured on MicroPython 1.21).
    pwm = PWM(Pin(6, Pin.OUT))
    assert not hasattr(pwm, "duty")


def test_pwm_duty_ns_roundtrip():
    pwm = PWM(Pin(6, Pin.OUT), freq=1000)
    pwm.duty_ns(500_000)
    assert pwm.duty_u16() == 32768
    assert 499_000 <= pwm.duty_ns() <= 501_000


def test_pwm_duty_ns_keyword_at_construction():
    pwm = PWM(Pin(6, Pin.OUT), freq=2000, duty_ns=125_000)
    assert pwm.duty_u16() == 16384


def test_pwm_duty_ns_past_the_period_saturates():
    pwm = PWM(Pin(6, Pin.OUT), freq=1000)
    pwm.duty_ns(5_000_000)
    assert pwm.duty_u16() == 65535


def test_pwm_init_keywords():
    pwm = PWM(Pin(6, Pin.OUT))
    pwm.init(freq=5000, duty_u16=16384)
    assert pwm.freq() == 5000
    assert pwm.duty_u16() == 16384


def test_pwm_invert_keyword():
    pwm = PWM(Pin(6, Pin.OUT), freq=1000, duty_u16=32768, invert=1)
    assert pwm.duty_u16() == 32768


# ── SPI ───────────────────────────────────────────────────────────────────  #

def test_spi_bitorder_constants():
    # Upstream rp2 values, measured on real firmware.
    assert SPI.MSB == 1
    assert SPI.LSB == 0
    assert SoftSPI.MSB == 1
    assert SoftSPI.LSB == 0


def test_spi_controller_name_is_absent():
    # SPI.CONTROLLER is declared by the shared stub but never defined by the
    # rp2 port -- its constructor has no role argument.
    assert not hasattr(SPI, "CONTROLLER")
    assert not hasattr(SoftSPI, "CONTROLLER")


def test_spi_instantiation():
    spi = SPI()
    assert spi is not None


def test_spi_write():
    spi = SPI()
    spi.write(0xAB)


def test_spi_read():
    # MicroPython's SPI.read(nbytes) returns a heap-allocated bytes object;
    # this layer refuses it at compile time and names readinto(buf).
    spi = SPI()
    with pytest.raises(CompileError, match="heap-allocated bytes"):
        spi.read(1)


def test_spi_write_readinto():
    # Upstream's only write_readinto is the buffer pair; the single-byte
    # overload was a PyMCU invention and is gone.
    spi = SPI()
    write_buf = bytearray(b"\xAB")
    read_buf = bytearray(1)
    spi.write_readinto(write_buf, read_buf)


def test_spi_constructor_form():
    # The documented MicroPython spelling (PyMCU/pymcu-micropython#4): used to
    # refuse both the id and every keyword.
    spi = SPI(0, baudrate=1000000, polarity=0, phase=0)
    spi.write(0xAB)


def test_spi_constructor_rejects_other_id():
    with pytest.raises(CompileError):
        SPI(1)


def test_spi_constructor_rejects_sck_mosi_miso():
    # This chip's SPI pins are fixed; sck=/mosi=/miso= are refused by name.
    with pytest.raises(CompileError):
        SPI(sck=Pin(2))


def test_spi_init_reconfigures():
    spi = SPI()
    spi.init(baudrate=2000000, polarity=1, phase=1)


def test_softspi_requires_pins():
    with pytest.raises(CompileError):
        SoftSPI(baudrate=200000)


def test_softspi_instantiation_and_transfer():
    sck = Pin(2, Pin.OUT)
    mosi = Pin(3, Pin.OUT)
    miso = Pin(4, Pin.IN)
    spi = SoftSPI(baudrate=200000, sck=sck, mosi=mosi, miso=miso)
    spi.write(0xAB)
    buf = bytearray(1)
    spi.readinto(buf)
    spi.deinit()


def test_softspi_write_readinto():
    sck = Pin(2, Pin.OUT)
    mosi = Pin(3, Pin.OUT)
    miso = Pin(4, Pin.IN)
    spi = SoftSPI(sck=sck, mosi=mosi, miso=miso)
    write_buf = bytearray(b"\x01\x02")
    read_buf = bytearray(2)
    spi.write_readinto(write_buf, read_buf)


# ── I2C ───────────────────────────────────────────────────────────────────  #

def test_i2c_instantiation():
    i2c = I2C()
    assert i2c is not None


def test_i2c_writeto():
    i2c = I2C()
    i2c.writeto(0x68, 0x00)


def test_i2c_readfrom():
    # MicroPython's readfrom(addr, nbytes) returns heap bytes; the layer
    # refuses it at compile time and names readfrom_into(addr, buf).
    i2c = I2C()
    with pytest.raises(CompileError, match="heap-allocated bytes"):
        i2c.readfrom(0x68, 1)


def test_i2c_scan_returns_int():
    # scan() refuses: upstream returns a list, which needs a heap. The
    # caller-owned-buffer form scan(buf, max_count) is the faithful shape.
    i2c = I2C()
    i2c._i2c.nack.update(range(1, 128))  # a bus with nothing on it
    with pytest.raises(CompileError, match="heap-allocated list"):
        i2c.scan()
    count = i2c.scan(bytearray(8), 8)
    assert isinstance(count, int)
    assert count == 0


def test_i2c_writeto_stop_false():
    # PyMCU/pymcu-micropython#14/#15: stop=False holds the bus for a following
    # readfrom*() instead of releasing it. stop is a plain, not keyword-only,
    # parameter (PyMCU/PyMCU#447: keyword args refused past one @inline overload).
    i2c = I2C()
    i2c.writeto(0x68, 0x00, 0)
    i2c.writeto(0x68, bytearray(b"\x01\x02"), 0)


def test_i2c_readfrom_into_stop_false():
    i2c = I2C()
    buf = bytearray(2)
    i2c.readfrom_into(0x68, buf, 0)


def test_i2c_raw_primitives():
    i2c = I2C()
    i2c.start()
    i2c.stop()
    acks = i2c.write(bytearray(b"\x01\x02"))
    assert isinstance(acks, int)
    buf = bytearray(2)
    i2c.readinto(buf)
    i2c.readinto(buf, 0)


def test_i2c_mem_helpers():
    i2c = I2C()
    i2c.writeto_mem(0x68, 0x00, bytearray(b"\x01"))
    buf = bytearray(2)
    i2c.readfrom_mem_into(0x68, 0x00, buf)
    i2c.readfrom_mem(0x68, 0x00, buf, 2)


def test_i2c_mem_helpers_reject_addrsize():
    i2c = I2C()
    with pytest.raises(CompileError):
        i2c.writeto_mem(0x68, 0x00, bytearray(b"\x01"), addrsize=16)
    with pytest.raises(CompileError):
        i2c.readfrom_mem_into(0x68, 0x00, bytearray(2), addrsize=16)


def test_i2c_writeto_raises_eio_on_address_nack():
    # MicroPython reports a failed transaction as OSError [Errno 5] EIO; the HAL
    # status used to be dropped, so a NACKed write looked like a good one.
    i2c = I2C()
    i2c._i2c.nack.add(0x3C)
    with pytest.raises(OSError) as e:
        i2c.writeto(0x3C, 0x00)
    assert str(e.value) == "[Errno 5] EIO"


def test_i2c_writeto_raises_eio_on_data_nack():
    i2c = I2C()
    i2c._i2c.nack_data = True
    with pytest.raises(OSError) as e:
        i2c.writeto(0x3C, 0x00)
    assert str(e.value) == "[Errno 5] EIO"


def test_i2c_writeto_buf_raises_eio_on_nack():
    i2c = I2C()
    i2c._i2c.nack.add(0x3C)
    with pytest.raises(OSError) as e:
        i2c.writeto(0x3C, bytearray(b"\x00\x01"))
    assert str(e.value) == "[Errno 5] EIO"


def test_i2c_writeto_stop_false_raises_eio_on_nack():
    i2c = I2C()
    i2c._i2c.nack.add(0x3C)
    with pytest.raises(OSError) as e:
        i2c.writeto(0x3C, 0x00, 0)
    assert str(e.value) == "[Errno 5] EIO"


def test_i2c_writeto_raises_eio_when_start_fails():
    i2c = I2C()
    i2c._i2c.fail_start = True
    with pytest.raises(OSError) as e:
        i2c.writeto(0x3C, 0x00, 0)
    assert str(e.value) == "[Errno 5] EIO"


def test_i2c_readfrom_raises_eio_on_nack():
    # The NACK path moved to readfrom_into -- readfrom(addr, nbytes) is the
    # heap-bytes spelling and refuses before it touches the bus.
    i2c = I2C()
    i2c._i2c.nack.add(0x3C)
    with pytest.raises(OSError) as e:
        i2c.readfrom_into(0x3C, bytearray(1))
    assert str(e.value) == "[Errno 5] EIO"


def test_i2c_readfrom_into_raises_eio_on_nack():
    i2c = I2C()
    i2c._i2c.nack.add(0x3C)
    with pytest.raises(OSError) as e:
        i2c.readfrom_into(0x3C, bytearray(2))
    assert str(e.value) == "[Errno 5] EIO"
    with pytest.raises(OSError):
        i2c.readfrom_into(0x3C, bytearray(2), 0)


def test_i2c_mem_helpers_raise_eio_on_nack():
    i2c = I2C()
    i2c._i2c.nack.add(0x3C)
    with pytest.raises(OSError) as e:
        i2c.writeto_mem(0x3C, 0x00, bytearray(b"\x01"))
    assert str(e.value) == "[Errno 5] EIO"
    with pytest.raises(OSError):
        i2c.readfrom_mem_into(0x3C, 0x00, bytearray(2))
    with pytest.raises(OSError):
        i2c.readfrom_mem(0x3C, 0x00, bytearray(2), 2)


def test_i2c_ack_path_raises_nothing():
    i2c = I2C()
    i2c.writeto(0x68, 0x00)
    i2c.writeto(0x68, bytearray(b"\x01\x02"))
    i2c.writeto(0x68, 0x00, 0)
    i2c.readfrom_into(0x68, bytearray(2))
    i2c.writeto_mem(0x68, 0x00, bytearray(b"\x01"))
    i2c.readfrom_mem_into(0x68, 0x00, bytearray(2))


# ── SoftI2C (machine module) ────────────────────────────────────────────── #

def test_softi2c_writeto_stop_false():
    scl = Pin(5, Pin.OUT)
    sda = Pin(4, Pin.OUT)
    i2c = SoftI2C(scl, sda)
    i2c.writeto(0x48, 0xA5, 0)
    i2c.writeto(0x48, bytearray(b"\x01\x02"), 0)


def test_softi2c_readfrom_into():
    scl = Pin(5, Pin.OUT)
    sda = Pin(4, Pin.OUT)
    i2c = SoftI2C(scl, sda)
    buf = bytearray(2)
    i2c.readfrom_into(0x48, buf)
    i2c.readfrom_into(0x48, buf, 0)


def test_softi2c_raw_primitives():
    scl = Pin(5, Pin.OUT)
    sda = Pin(4, Pin.OUT)
    i2c = SoftI2C(scl, sda)
    i2c.start()
    i2c.stop()
    acks = i2c.write(bytearray(b"\x01"))
    assert isinstance(acks, int)
    buf = bytearray(2)
    i2c.readinto(buf)


def test_softi2c_mem_helpers():
    scl = Pin(5, Pin.OUT)
    sda = Pin(4, Pin.OUT)
    i2c = SoftI2C(scl, sda)
    i2c.writeto_mem(0x48, 0x00, bytearray(b"\x01"))
    buf = bytearray(2)
    i2c.readfrom_mem_into(0x48, 0x00, buf)
    i2c.readfrom_mem(0x48, 0x00, buf, 2)


def test_softi2c_raises_eio_on_nack():
    # Same OSError as the hardware bus: a NACK is an ACK bit of 1 here.
    scl = Pin(5, Pin.OUT)
    sda = Pin(4, Pin.OUT)
    i2c = SoftI2C(scl, sda)
    i2c._bus.nack.add(0x3C)
    with pytest.raises(OSError) as e:
        i2c.writeto(0x3C, 0x00)
    assert str(e.value) == "[Errno 5] EIO"
    with pytest.raises(OSError):
        i2c.writeto(0x3C, 0x00, 0)
    with pytest.raises(OSError):
        i2c.writeto(0x3C, bytearray(b"\x00"))
    with pytest.raises(OSError):
        i2c.readfrom_into(0x3C, bytearray(2))
    with pytest.raises(OSError):
        i2c.writeto_mem(0x3C, 0x00, bytearray(b"\x01"))
    with pytest.raises(OSError):
        i2c.readfrom_mem_into(0x3C, 0x00, bytearray(2))
    with pytest.raises(OSError):
        i2c.readfrom_mem(0x3C, 0x00, bytearray(2), 2)


def test_softi2c_raises_eio_on_data_nack():
    scl = Pin(5, Pin.OUT)
    sda = Pin(4, Pin.OUT)
    i2c = SoftI2C(scl, sda)
    i2c._bus.nack_data = True
    with pytest.raises(OSError) as e:
        i2c.writeto(0x3C, 0x00)
    assert str(e.value) == "[Errno 5] EIO"


def test_i2c_deinit_names_are_absent():
    # I2C.deinit / SoftI2C.deinit are stub declarations the rp2 firmware does
    # not define (measured on MicroPython 1.21) -- there is no bus teardown
    # method upstream on this port.
    assert not hasattr(I2C, "deinit")
    assert not hasattr(SoftI2C, "deinit")


# ── Module-level constants ────────────────────────────────────────────────  #

def test_sleep_mode_names_are_absent():
    # IDLE / SLEEP / DEEPSLEEP are not module members on upstream rp2 -- the
    # port ships the idle()/lightsleep()/deepsleep() functions and no numeric
    # sleep-mode constants at module level.
    import pymcu_micropython.machine as machine_mod
    for name in ("IDLE", "SLEEP", "DEEPSLEEP"):
        assert not hasattr(machine_mod, name), name


def test_reset_cause_constants():
    # Upstream rp2 values, measured on real firmware.
    assert PWRON_RESET == 1
    assert WDT_RESET   == 3


def test_esp32_reset_and_wake_names_are_absent():
    # HARD_RESET / SOFT_RESET / DEEPSLEEP_RESET and the *_WAKE codes are
    # esp32-port spellings; upstream rp2 exports none of them.
    import pymcu_micropython.machine as machine_mod
    for name in ("HARD_RESET", "SOFT_RESET", "DEEPSLEEP_RESET",
                 "PIN_WAKE", "RTC_WAKE", "WLAN_WAKE"):
        assert not hasattr(machine_mod, name), name


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


def test_timer_irq_names_are_absent():
    # Timer.irq()/start()/IRQ_OVF/IRQ_COMPA are PyMCU HAL spellings; upstream
    # rp2 Timer attaches its callback through init(callback=...) and defines
    # none of them.
    t = Timer(0)
    for name in ("irq", "start", "IRQ_OVF", "IRQ_COMPA"):
        assert not hasattr(t, name) and not hasattr(Timer, name), name


# ── Timer instantiation and methods ──────────────────────────────────────  #

def test_timer_instantiation():
    t = Timer(0)
    assert t is not None


def test_timer_with_prescaler():
    t = Timer(1, 256)
    assert t is not None


def test_timer_deinit():
    t = Timer(0)
    t.deinit()  # must not raise


def test_timer_init():
    t = Timer(0)
    t.init()  # stop + restart; must not raise


# ── Timer.init(period, mode, callback) ───────────────────────────────────  #

def test_timer_init_with_period():
    t = Timer(1)
    t.init(period=100, mode=Timer.PERIODIC, callback=lambda: None)


def test_timer_init_period_short():
    # period <= 262 ms -> prescaler=64 path
    t = Timer(1)
    t.init(period=50, callback=lambda: None)


def test_timer_init_period_long():
    # period > 262 ms -> prescaler=1024 path
    t = Timer(1)
    t.init(period=500, callback=lambda: None)


def test_timer_init_no_period_uses_prescaler():
    # No period -> plain start() path; prescaler override accepted
    t = Timer(0)
    t.init(prescaler=256)


def test_timer_init_no_period_no_args():
    t = Timer(0)
    t.init()  # stop + start; must not raise


def test_timer_init_one_shot():
    t = Timer(1)
    t.init(period=200, mode=Timer.ONE_SHOT, callback=lambda: None)


# ── Timer(-1, period=ms, callback=cb) constructor form ───────────────────  #

def test_timer_auto_id_with_period():
    # Timer(-1, ...) in MicroPython; use 255 as sentinel in PyMCU
    t = Timer(255, period=100, callback=lambda: None)
    assert t is not None


def test_timer_constructor_period_callback():
    t = Timer(1, period=500, mode=Timer.PERIODIC, callback=lambda: None)
    assert t is not None


def test_timer_constructor_no_period_still_works():
    t = Timer(0)
    assert t is not None


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
