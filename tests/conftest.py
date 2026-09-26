"""
Inject pymcu.hal.* stubs into sys.modules so that pymcu_micropython modules
can be imported in standard CPython without MCU hardware.

This file is loaded by pytest before any test module, so the mocks are in place
when the package-under-test runs its top-level imports.
"""
import sys
from pymcu.exceptions import CompileError
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

        def __init__(self, name, mode=1, pull=0):
            self._name = name
            self._mode = mode
            self._pull = pull
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
            if mode is not None and mode != -1:
                self._mode = mode

        def mode(self, m=None):
            if m is None:
                return self._mode
            self._mode = m

        def pull(self, p):                          pass
        def irq(self, trigger=None, handler=None):          pass
        def pulse_in(self, state, timeout_us=1000): return 50

    class _MockUART:
        # Records the frame it was configured with, the bytes written, and serves
        # read_timeout() from `rx` (-1 once it runs dry, as the HAL does on a timeout).
        def __init__(self, baudrate=9600, bits=8, parity=0, stop=1):
            self.config = (baudrate, bits, parity, stop)
            self.sent = []
            self.rx = []
            self.waits = []
            self.enabled = True
        def reinit(self, baudrate=9600, bits=8, parity=0, stop=1):
            self.config = (baudrate, bits, parity, stop)
        def deinit(self):        self.enabled = False
        def tx_empty(self):      return 1
        def read_timeout(self, ms):
            self.waits.append(ms)
            return self.rx.pop(0) if self.rx else -1
        def write(self, data):   self.sent.append(data)
        def read(self):          return 0
        def write_str(self, s):  pass
        def println(self, s):    pass
        def print_byte(self, v): pass
        def irq(self, handler):  pass
        def available(self):     return 0
        def read_line(self, buf, max_len): return 0

    class _MockAnalogPin:
        def __init__(self, pin): pass
        def start(self):         pass
        def read(self):          return 0

    class _MockPWM:
        def __init__(self, pin, duty=0, freq=1000, invert=0, duty_u16=0): pass
        def start(self):          pass
        def stop(self):           pass
        def set_duty(self, d):    pass
        def set_duty_u16(self, d): pass
        def set_freq(self, f):    pass

    class _MockSPI:
        def __init__(self, mode=0, cs="", baudrate=4000000, polarity=0, phase=0, lsb_first=0): pass
        def configure(self, baudrate=4000000, polarity=0, phase=0, lsb_first=0): pass
        def transfer(self, data): return 0
        def write(self, data):    pass
        def write_bytes(self, buf, n):                 pass
        def readinto_n(self, buf, n, write_byte):      pass
        def write_readinto_n(self, wbuf, rbuf, n):     pass
        def select(self):         pass
        def deselect(self):       pass

    class _MockSoftSPI:
        def __init__(self, sck, mosi, miso, mode=0, cs=None, baudrate=500): pass
        def set_baudrate(self, baudrate): pass
        def transfer(self, data): return 0
        def write(self, data):    pass

    class _MockI2C:
        # In step with pymcu.hal.i2c.I2C: start()/write() return the TWI status the
        # hardware leaves in TWSR (0x08/0x10 START, 0x18 SLA+W ACK, 0x28 data ACK,
        # 0x40 SLA+R ACK; 0x20/0x30/0x48 NACKs, 0xFF bus timeout), and the composite
        # helpers return 1 on a fully ACKed transaction.
        START     = 0x08
        RESTART   = 0x10
        SLA_ACK   = 0x18
        SLA_NACK  = 0x20
        DATA_ACK  = 0x28
        SLA_R_ACK = 0x40

        def __init__(self, addr=0, general_call=0, freq=100000, pullups=True):
            # Test knobs: 7-bit addresses that NACK their SLA, a flag that NACKs
            # every data byte after an acknowledged address, and a wedged START.
            self.freq = freq
            self.nack: set = set()
            self.nack_data = False
            self.fail_start = False
            self._expect_sla = False

        def ping(self, addr):        return 0 if addr in self.nack else 1
        def write_bytes(self, addr, buf, n):
            if self.fail_start: return 0xFF
            return 0 if addr in self.nack or self.nack_data else 1
        def writebyte(self, addr, b):
            if self.fail_start: return 0xFF
            return 0x20 if addr in self.nack else (0x30 if self.nack_data else 1)
        def write_to(self, addr, d):
            if self.fail_start: return 0xFF
            return 0 if addr in self.nack or self.nack_data else 1
        def read_from(self, addr):   return 0
        def read_ack(self):          return 0
        def read_nack(self):         return 0
        def read_n(self, addr, buf, n):
            if self.fail_start: return 0xFF
            return 0 if addr in self.nack else 1
        def start(self):
            self._expect_sla = True
            return 0xFF if self.fail_start else self.START
        def stop(self):
            self._expect_sla = False
        def write(self, data):
            if self._expect_sla:
                self._expect_sla = False
                if (data >> 1) in self.nack:
                    return 0x48 if data & 1 else self.SLA_NACK
                return self.SLA_R_ACK if data & 1 else self.SLA_ACK
            return 0x30 if self.nack_data else self.DATA_ACK
        def read(self):              return 0
        def writeto_mem(self, addr, reg, data):
            if self.fail_start: return 0xFF
            return 0 if addr in self.nack or self.nack_data else 1
        def readfrom_mem(self, addr, reg, buf, n):
            if self.fail_start: return 0xFF
            return 0 if addr in self.nack else 1

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
        # In step with pymcu.hal.softi2c.SoftI2C: write() returns the ACK bit
        # (0 = ACK, 1 = NACK) and the composite helpers return 1 on a fully
        # ACKed transaction.
        def __init__(self, scl, sda, half_us=5):
            # Test knobs: 7-bit addresses that NACK their SLA, and a flag that
            # NACKs every data byte after an acknowledged address.
            self.nack: set = set()
            self.nack_data = False
            self._expect_sla = False

        def init(self):                          pass
        def start(self):                         self._expect_sla = True
        def stop(self):                          self._expect_sla = False
        def write(self, data):
            if self._expect_sla:
                self._expect_sla = False
                return 1 if (data >> 1) in self.nack else 0
            return 1 if self.nack_data else 0
        def read(self, send_ack):                return 0
        def write_to(self, addr, data):
            return 0 if addr in self.nack or self.nack_data else 1
        def write_bytes(self, addr, buf, n):
            return 0 if addr in self.nack or self.nack_data else 1
        def read_from(self, addr):               return 0
        def ping(self, addr):                    return 0 if addr in self.nack else 1

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
    _reg("timer",    Timer=_MockTimer, millis=lambda: 0, micros=lambda: 0, millis_init=lambda: None)
    _reg("watchdog", Watchdog=_MockWatchdog)
    # The global interrupt flag, modelled so a nested critical section can be
    # checked: save_and_disable_interrupts() answers the I-flag (0x80 when on)
    # and restore_interrupts() puts back exactly what it is given.
    irq_flag = {"on": 0x80}

    def _save_and_disable():
        state = irq_flag["on"]
        irq_flag["on"] = 0
        return state

    def _restore(state):
        irq_flag["on"] = 0x80 if state else 0

    _reg("irq",
         enable_interrupts=lambda: irq_flag.update(on=0x80),
         disable_interrupts=lambda: irq_flag.update(on=0),
         save_and_disable_interrupts=_save_and_disable,
         restore_interrupts=_restore,
         irq_flag=irq_flag)
    _reg("power",
         sleep_idle=lambda: None,
         sleep_power_save=lambda: None,
         sleep_power_down=lambda: None)
    _reg("softspi",  SoftSPI=_MockSoftSPI)
    # The AVR package machine.py reaches into for the board pin table, and the
    # WiFi HAL network.py wraps; neither has a hardware side under CPython.
    _reg("avr")
    def _board_pin_name(n):
        if n < 8:
            return f"PD{n}"
        if n < 14:
            return f"PB{n - 8}"
        if n < 20:
            return f"PC{n - 14}"   # A0-A5, as the Uno table in the HAL has them
        raise CompileError(f"pin {n} is not a pin of this board")

    _reg("avr.gpio", board_pin_name=_board_pin_name)
    _reg(
        "wifi",
        CYW43=type("CYW43", (), {
            "init": lambda self: None,
            "join_open": lambda self, ssid: None,
            "settle": lambda self: None,
        }),
        WiFi=type("WiFi", (), {}),
    )
    _reg("softi2c",  SoftI2C=_MockSoftI2C)
    _reg("softspi",  SoftSPI=_MockSoftSPI)
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

    # machine.py branches on __CHIP__.arch at import time, so the stub has to be an
    # object with that attribute -- a bare "atmega328p" string raised AttributeError
    # before the module finished loading.
    class _ChipInfo:
        name = "atmega328p"
        arch = "avr"

    chips = ModuleType("pymcu.chips")
    chips.__CHIP__ = _ChipInfo()
    chips.__FREQ__ = 16_000_000
    chips.device_info = lambda: _DeviceInfo()
    sys.modules["pymcu.chips"] = chips


_install_hal_mocks()

# The compiler binds _set_irq_zca_arg as an intrinsic (it hands an instance to an ISR); under
# CPython it is a builtin that does nothing.
import builtins as _builtins
_builtins._set_irq_zca_arg = lambda handler, inst: None
