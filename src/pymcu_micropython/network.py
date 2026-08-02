# MicroPython-compat network.WLAN over the CYW43439 (Pico 2 W). Universal source; the
# per-arch radio lives in the HAL (pymcu.hal.wifi -> hal/rp2350/cyw43).
from pymcu.hal.wifi import CYW43
from pymcu.types import uint8, inline, const
from pymcu.exceptions import CompileError

STA_IF = 0
AP_IF = 1


class WLAN:
    @inline
    def __init__(self, interface: uint8 = 0):
        self._hw = CYW43()

    @inline
    def active(self, on: uint8 = 1):
        if on != 0:
            self._hw.init()

    @inline
    def connect(self, ssid: const[str], key: const[str] = ""):
        # The radio only knows how to join an open network (join_open sends no
        # PSK), so accepting a key would silently drop it. Same guard as the HAL.
        if key != "":
            raise CompileError("WiFi: WPA is not supported yet; connect() can only join open networks -- leave key empty")
        self._hw.join_open(ssid)
        self._hw.settle()

    @inline
    def isconnected(self) -> uint8:
        return 1
