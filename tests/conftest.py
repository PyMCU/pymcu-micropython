"""
Inject pymcu.hal.* stubs into sys.modules so that pymcu_micropython modules
can be imported in standard CPython without MCU hardware.

This file is loaded by pytest before any test module, so the mocks are in place
when the package-under-test runs its top-level imports.
"""
import sys
from types import ModuleType
from unittest.mock import MagicMock


def _install_hal_mocks() -> None:
    # Guard: only install once per process.
    if "pymcu.hal" in sys.modules:
        return

    # --- concrete mock classes ------------------------------------------ #

    class _MockPin:
        IN = 1
        OUT = 0
        OPEN_DRAIN = 2
        PULL_UP = 1

        def __init__(self, name, mode=1):
            self._name = name
            self._mode = mode
            self._v = 0

        def high(self):   self._v = 1
        def low(self):    self._v = 0
        def on(self):     self._v = 1
        def off(self):    self._v = 0
        def toggle(self): self._v ^= 1

        def value(self, x=None):
            if x is None:
                return self._v
            self._v = x
            return x

        def init(self, mode=None, pull=None, **kw):
            if mode is not None and mode != 255:
                self._mode = mode

        def mode(self, m=None):
            if m is None:
                return self._mode
            self._mode = m

        def pull(self, p):                          pass
        def irq(self, trigger=None, handler=None):          pass
        def pulse_in(self, state, timeout_us=1000): return 50

    class _MockUART:
        def __init__(self, baudrate=9600): pass
        def write(self, data):   pass
        def read(self):          return 0
        def write_str(self, s):  pass
        def println(self, s):    pass
        def print_byte(self, v): pass

    class _MockAnalogPin:
        def __init__(self, pin): pass
        def start(self):         pass
        def read(self):          return 0

    class _MockPWM:
        def __init__(self, pin, duty=0): pass
        def start(self):          pass
        def stop(self):           pass
        def set_duty(self, d):    pass

    class _MockSPI:
        def __init__(self, cs=""): pass
        def transfer(self, data): return 0
        def write(self, data):    pass
        def select(self):         pass
        def deselect(self):       pass

    class _MockI2C:
        def __init__(self):          pass
        def ping(self, addr):        return 0
        def write_to(self, addr, d): return 0
        def read_from(self, addr):   return 0
        def read_nack(self):         return 0
        def start(self):             pass
        def stop(self):              pass
        def write(self, data):       pass
        def read(self):              return 0

    class _MockTimer:
        IRQ_OVF   = 1
        IRQ_COMPA = 2
        def __init__(self, n, prescaler=64):    pass
        def start(self):                        pass
        def stop(self):                         pass
        def clear(self):                        pass
        def set_compare(self, value):           pass
        def reinit(self, prescaler):            pass
        def irq(self, handler, mode=1):         pass

    class _MockWatchdog:
        def __init__(self, timeout_ms=500): pass
        def enable(self):                   pass
        def disable(self):                  pass
        def feed(self):                     pass

    class _MockSoftSPI:
        CONTROLLER = 0
        PERIPHERAL = 1
        def __init__(self, sck, mosi, miso, mode=0, cs=None, baudrate=500): pass
        def transfer(self, data):   return 0
        def write(self, data):      pass
        def exchange(self, data):   return 0
        def receive(self):          return 0
        def cs_asserted(self):      return 0
        def select(self):           pass
        def deselect(self):         pass

    class _MockSoftI2C:
        def __init__(self, scl, sda, half_us=5): pass
        def init(self):                          pass
        def start(self):                         pass
        def stop(self):                          pass
        def write(self, data):                   return 0
        def read(self, send_ack):                return 0
        def write_to(self, addr, data):          return 0
        def read_from(self, addr):               return 0
        def ping(self, addr):                    return 0

    class _MockEEPROM:
        def __init__(self):           pass
        def write(self, addr, value): pass
        def read(self, addr):         return 0

    # --- register hal sub-modules --------------------------------------- #

    hal = ModuleType("pymcu.hal")
    sys.modules["pymcu.hal"] = hal

    def _reg(name: str, **attrs) -> ModuleType:
        m = ModuleType(f"pymcu.hal.{name}")
        for k, v in attrs.items():
            setattr(m, k, v)
        sys.modules[f"pymcu.hal.{name}"] = m
        setattr(hal, name, m)
        return m

    _reg("gpio",     Pin=_MockPin)
    _reg("uart",     UART=_MockUART)
    _reg("adc",      AnalogPin=_MockAnalogPin)
    _reg("pwm",      PWM=_MockPWM)
    _reg("spi",      SPI=_MockSPI)
    _reg("i2c",      I2C=_MockI2C)
    _reg("timer",    Timer=_MockTimer, millis=lambda: 0, millis_init=lambda: None)
    _reg("watchdog", Watchdog=_MockWatchdog)
    _reg("irq",
         enable_interrupts=lambda: None,
         disable_interrupts=lambda: None)
    _reg("power",
         sleep_idle=lambda: None,
         sleep_power_save=lambda: None,
         sleep_power_down=lambda: None)
    _reg("softspi",  SoftSPI=_MockSoftSPI)
    _reg("softi2c",  SoftI2C=_MockSoftI2C)
    _reg("eeprom",   EEPROM=_MockEEPROM)

    # --- pymcu.time (time.py / utime.py import delay_ms, delay_us) ------ #
    # The real pymcu.time imports __CHIP__ from pymcu.chips at module load,
    # which is a compile-time constant injected by the compiler.  It is not
    # present at runtime in CPython, so we replace the whole module.
    time_mod = ModuleType("pymcu.time")
    time_mod.delay_ms = lambda ms: None
    time_mod.delay_us = lambda us: None
    sys.modules["pymcu.time"] = time_mod

    # --- pymcu.chips ---------------------------------------------------- #
    class _DeviceInfo:
        frequency = 16_000_000

    chips = ModuleType("pymcu.chips")
    chips.__CHIP__ = "atmega328p"
    chips.__FREQ__ = 16_000_000
    chips.device_info = lambda: _DeviceInfo()
    sys.modules["pymcu.chips"] = chips


_install_hal_mocks()
