# pymcu-micropython

MicroPython standard-library flavor for **PyMCU** — an AOT (ahead-of-time) Python compiler that targets microcontrollers.

## What is this?

`pymcu-micropython` is a drop-in compatibility layer that lets you write firmware using the familiar [MicroPython](https://micropython.org/) API (`machine`, `utime`, `micropython` modules) while compiling it to bare-metal machine code with PyMCU.  All classes and functions are implemented as zero-cost abstractions (ZCA): they are marked `@inline` so that no SRAM instance structs, no stack frames, and no interpreter overhead are introduced — the compiler resolves everything at compile time.

## Modules

| Module | MicroPython equivalent | Description |
|--------|------------------------|-------------|
| `machine` | `machine` | `Pin`, `UART`, `ADC`, `PWM`, `SPI`, `I2C`, `Timer`, `WDT`, `Signal` |
| `utime` | `utime` / `time` | `sleep_ms()`, `sleep_us()`, `sleep()`, `ticks_ms()`, `ticks_us()`, `ticks_diff()`, `ticks_add()` |
| `micropython` | `micropython` | `const()`, `@native`, `@viper` stubs |
| `os` | `os` / `uos` | `uname()` only -- compile-time port facts (see below) |
| `framebuf` | `framebuf` | `FrameBuffer`, `FrameBuffer1` over a caller-owned `bytearray`: `fill`, `pixel`, `hline`, `vline`, `line`, `rect`, `fill_rect`, `text`, `scroll`, `blit`, in every upstream format |
| `sys` | `sys` / `usys` | `implementation`, `platform`, `version`, `version_info`, `byteorder`, `maxsize` -- compile-time port facts (see below) |

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

## API parity with MicroPython

`tests/parity/` compares this layer's real API surface against `micropython-rp2-stubs` (the
RP2/Pico stub package) symbol by symbol. Where this layer deliberately differs, the reason is
either a hardware/architecture limit of this class of AVR chip -- documented in
[`docs/limitations.md`](docs/limitations.md) -- or a real, tracked gap referenced from
[`docs/parity.md`](docs/parity.md), which the suite regenerates.

### `os` and `sys`: compile-time introspection only

`os` provides `uname()` and `sys` provides `implementation` (`name` and `version`),
`platform`, `version`, `version_info`, `byteorder` and `maxsize`. The introspection
names are the `sys` reads the MicroPython library ecosystem reaches for at branch
time to tell ports apart (`if sys.platform == "rp2":`,
`if sys.implementation.name == "micropython":`, `if uname().sysname == "rp2":`); the
compiler substitutes the real per-board values at every read site, so a compiled
program never runs these bodies. `version`, `byteorder` and `maxsize` are plain
constants -- the pinned API surface and the target's own word size/endianness --
and `version_info` answers `(3, 4, 0)` at the `sys.version_info[i]` read site only
(a tuple attribute has no honest module-level form, so the bare attribute refuses,
the same contract `implementation.version` holds). `uos` and `usys` are the same
modules under MicroPython's own u-spelling.

Everything else upstream's `os` documents -- `chdir`, `getcwd`, `ilistdir`, `listdir`,
`mkdir`, `mount`, `remove`, `rename`, `rmdir`, `stat`, `statvfs`, `sync`, `umount`,
`unlink`, `VfsFat`, `VfsLfs2` -- needs a filesystem this target does not have.
`urandom` needs an entropy source there is no API for, and `dupterm` needs a stream
object to redirect, so those stay out too. Everything else upstream's `sys` documents
-- `argv`, `exit`, `modules`, `path`, `print_exception`, `ps1`, `ps2`, `stdin`,
`stdout`, `stderr` -- needs a runtime PyMCU does not have (a module table, a
filesystem search path, stream objects, command-line arguments, a REPL). None of
them are here: a stub that returns a plausible value is worse than an absence, and
a name that exists here but not on a board is the failure this layer exists to
prevent.

### `uasyncio`: the cooperative subset

`uasyncio` re-exports `pymcu.asyncio`'s surface -- `sleep`, `sleep_ms`, `run`, `gather`,
`ticks` -- because those are the waits and drivers a compiled coroutine actually runs.
Everything else upstream's `uasyncio` has -- `CancelledError`, `TimeoutError`, `Event`,
`Lock`, `ThreadSafeFlag`, `IOQueue`, `TaskQueue`, `Task`, `Loop`, `SingletonGenerator`,
`create_task`, `current_task`, `get_event_loop`, `new_event_loop`, `run_until_complete`,
`wait_for`, `wait_for_ms`, `StreamReader`, `StreamWriter`, `open_connection`,
`start_server` -- is not here: the waitable/task primitives land with the compile-time
scheduler work, and the stream half needs sockets this target does not have.

Two stub artifacts to read the suite by, because the `uasyncio` stub is `from asyncio
import *` over the shared CPython typeshed asyncio rather than a MicroPython-shaped
stub: parameters like `loop=`, `debug=`, `result=` and `coro_or_futureN` exist nowhere
on a board (real `uasyncio.run` is `run(coro)`, `uasyncio.sleep` is `sleep(t)`), and
`gather` is deliberately `gather(a, b)` here -- a coroutine state machine is a type,
not a runtime value a variadic form could iterate (pymcu.asyncio's own docstring
explains the fixed arity and points at `create_task` for three or more).

The suite runs on every push and PR via `.github/workflows/ci.yml` (pure CPython, no compiler
needed). CI also checks out `PyMCU/PyMCU` and points at its `lib/` the same way "Running the
tests" below does, so it exercises the same `pymcu-stdlib` this repo's own tests need --
remove that checkout once a `pymcu-stdlib` release includes the fix (PyMCU/PyMCU#437).

## Running the tests

```sh
uv run --with pytest python -m pytest tests/parity -q
```

runs the parity suite alone (what CI runs). The full suite, `tests/` (the layer's own unit and
integration tests), needs `pymcu.types.inline`'s CPython overload dispatch -- the mechanism
that lets `machine.Pin`'s four `__init__` overloads (and every other overloaded method this
layer defines) resolve correctly when imported as ordinary Python, the same way `pymcuc`
resolves them at compile time. That dispatch has been in `pymcu-stdlib` since PyMCU's
`7dcc1c2c`, but the version on PyPI has not been re-released with it yet, so the plain
`pymcu-stdlib>=...` dependency this project installs predates the fix and every test that
constructs more than one overload of the same method fails with a wrong-arity `TypeError`.
Point `uv` at a `PyMCU` checkout's stdlib instead, until a `pymcu-stdlib` release includes it
(sibling checkout, `~/Repos/PyMCU` next to this repo):

```sh
uv run --with pytest --with-editable ~/Repos/PyMCU/lib python -m pytest tests -q
```

`uv run pytest` alone (no `--with pytest`) is never correct here either: it falls back to
whatever Python `uv tool` itself runs on, which can have an unrelated, older `pymcu` on its
own path.

## License

See [LICENSE](LICENSE) for details.
