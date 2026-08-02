# MicroPython-compat umqtt.simple.MQTTClient over the CYW43439 WiFi stack. Publishes a
# numeric reading to a fixed topic ("dht") using the HAL's built-in TCP+MQTT publish.
from pymcu.hal.wifi import CYW43
from pymcu.types import uint32, inline, const


class MQTTClient:
    @inline
    def __init__(self, wlan, client_id: const[str] = "pm", server: const[str] = ""):
        # Share the already-connected radio from the WLAN object.
        self._hw = wlan._hw

    @inline
    def connect(self) -> uint32:
        return 0

    @inline
    def publish(self, value: uint32):
        self._hw.mqtt_publish(value)

    @inline
    def disconnect(self):
        pass
