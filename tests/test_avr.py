from pymcu_micropython.machine import Pin
from pymcu_micropython.avr import EEPROM, SoftSPI, SoftI2C


# ── EEPROM ────────────────────────────────────────────────────────────────  #

def test_eeprom_instantiation():
    ee = EEPROM()
    assert ee is not None


def test_eeprom_write():
    ee = EEPROM()
    ee.write(0, 42)   # must not raise


def test_eeprom_read_returns_int():
    ee = EEPROM()
    val = ee.read(0)
    assert isinstance(val, int)


def test_eeprom_read_default_zero():
    ee = EEPROM()
    assert ee.read(0) == 0   # mock always returns 0


def test_eeprom_write_then_read():
    # In CPython the mock does not persist values; just verify it does not raise.
    ee = EEPROM()
    ee.write(10, 0xFF)
    ee.read(10)


# ── SoftSPI ───────────────────────────────────────────────────────────────  #

def test_softspi_constants():
    assert SoftSPI.CONTROLLER == 0
    assert SoftSPI.PERIPHERAL == 1


def test_softspi_instantiation():
    sck  = Pin(13, Pin.OUT)
    mosi = Pin(11, Pin.OUT)
    miso = Pin(12, Pin.IN)
    spi  = SoftSPI(sck, mosi, miso)
    assert spi is not None


def test_softspi_with_baudrate():
    sck  = Pin(13, Pin.OUT)
    mosi = Pin(11, Pin.OUT)
    miso = Pin(12, Pin.IN)
    spi  = SoftSPI(sck, mosi, miso, baudrate=250)
    assert spi is not None


def test_softspi_transfer_returns_int():
    sck  = Pin(13, Pin.OUT)
    mosi = Pin(11, Pin.OUT)
    miso = Pin(12, Pin.IN)
    spi  = SoftSPI(sck, mosi, miso)
    val  = spi.transfer(0xA5)
    assert isinstance(val, int)


def test_softspi_write():
    sck  = Pin(13, Pin.OUT)
    mosi = Pin(11, Pin.OUT)
    miso = Pin(12, Pin.IN)
    spi  = SoftSPI(sck, mosi, miso)
    spi.write(0x55)   # must not raise


def test_softspi_select_deselect():
    sck  = Pin(13, Pin.OUT)
    mosi = Pin(11, Pin.OUT)
    miso = Pin(12, Pin.IN)
    spi  = SoftSPI(sck, mosi, miso)
    spi.select()
    spi.deselect()


# ── SoftI2C ───────────────────────────────────────────────────────────────  #

def test_softi2c_instantiation():
    scl = Pin(5, Pin.OUT)
    sda = Pin(4, Pin.OUT)
    i2c = SoftI2C(scl, sda)
    assert i2c is not None


def test_softi2c_with_freq():
    scl = Pin(5, Pin.OUT)
    sda = Pin(4, Pin.OUT)
    i2c = SoftI2C(scl, sda, freq=400000)
    assert i2c is not None


def test_softi2c_scan_returns_int():
    scl = Pin(5, Pin.OUT)
    sda = Pin(4, Pin.OUT)
    i2c = SoftI2C(scl, sda)
    count = i2c.scan()
    assert isinstance(count, int)
    assert count == 0   # mock ping always returns 0


def test_softi2c_writeto():
    scl = Pin(5, Pin.OUT)
    sda = Pin(4, Pin.OUT)
    i2c = SoftI2C(scl, sda)
    ack = i2c.writeto(0x48, 0xA5)
    assert isinstance(ack, int)


def test_softi2c_readfrom():
    scl = Pin(5, Pin.OUT)
    sda = Pin(4, Pin.OUT)
    i2c = SoftI2C(scl, sda)
    val = i2c.readfrom(0x48)
    assert isinstance(val, int)


def test_softi2c_ping():
    scl = Pin(5, Pin.OUT)
    sda = Pin(4, Pin.OUT)
    i2c = SoftI2C(scl, sda)
    result = i2c.ping(0x48)
    assert result == 0   # mock always returns 0
