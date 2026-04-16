# pymcu-micropython

MicroPython standard-library flavor for **PyMCU** — an AOT (ahead-of-time) Python compiler that targets microcontrollers.

## What is this?

`pymcu-micropython` is a drop-in compatibility layer that lets you write firmware using the familiar [MicroPython](https://micropython.org/) API (`machine`, `utime`, `micropython` modules) while compiling it to bare-metal machine code with PyMCU.  All classes and functions are implemented as zero-cost abstractions (ZCA): they are marked `@inline` so that no SRAM instance structs, no stack frames, and no interpreter overhead are introduced — the compiler resolves everything at compile time.

## Modules

| Module | MicroPython equivalent | Description |
|--------|------------------------|-------------|
| `machine` | `machine` | `Pin`, `UART`, `ADC`, `PWM`, `SPI`, `I2C` |
| `utime` | `utime` / `time` | `sleep_ms()`, `sleep_us()`, `sleep()`, `ticks_ms()`, `ticks_diff()` |
| `micropython` | `micropython` | `const()`, `@native`, `@viper` stubs |

## Installation

```sh
pip install pymcu-micropython
```

Or add it as a dependency in your project's `pyproject.toml`:

```toml
[project]
dependencies = [
    "pymcu>=0.1.0a1",
    "pymcu-stdlib>=0.1.0a1",
    "pymcu-micropython>=0.1.0a1",
]
```

## Quick start

The API is intentionally identical to MicroPython, so existing MicroPython sketches work without modification:

```python
from machine import Pin
from utime import sleep_ms

def main():
    led = Pin(13, Pin.OUT)   # Arduino Uno built-in LED (D13 = PB5)
    while True:
        led.value(1)
        sleep_ms(500)
        led.value(0)
        sleep_ms(500)
```

Compile and flash with PyMCU:

```sh
pymcu build
pymcu flash
```

## Examples

| Example | Description |
|---------|-------------|
| [`examples/blink`](examples/blink) | Blink the built-in LED at 1 Hz |
| [`examples/adc-read`](examples/adc-read) | Read a potentiometer and print values over UART |
| [`examples/uart-echo`](examples/uart-echo) | Echo received bytes back over UART |

## Supported boards

The library currently ships pin-mapping support for:

- **Arduino Uno** (ATmega328P)

Additional boards can be added by contributing a file under `src/pymcu_micropython/boards/`.

## License

See [LICENSE](LICENSE) for details.
