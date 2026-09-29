# Changelog — pymcu-micropython

## 0.1.0b1 (re-frozen from main, 2026-09-29)

Beta 1 ships from `main` at `9f602f0` today. Ten commits landed since the
2026-09-26 re-freeze, all in `machine`, closing most of the API-parity gap
the corpus/parity suites had flagged: constructor keyword arguments the
layer used to refuse, and two silent-wrong-value bugs.

### Added

- **machine**: `I2C.writevto` and `SoftI2C.writevto` (`writevto(addr, vector, stop=True, /)`),
  writing every buffer of a tuple or list back to back after one START, ACK-counted and
  raising `OSError` on a NACK like `writeto`. The vector is walked by literal index (up to
  eight buffers); a vector bound to a name is still refused by the compiler, so the upstream
  SSD1306 driver (which keeps its vector in a field) does not compile yet.

### Fixed

- **machine**: `I2C`/`SoftI2C` default to upstream's 400 kHz (`freq=400000`), not 100 kHz;
  only the layer's default changed; `busio.I2C`'s own 100 kHz default is unaffected.
- **machine**: `PWM.freq(value)` retunes a Timer1 exact-frequency channel and reprograms
  duty against the new period, instead of being refused; `PWM(pin); pwm.freq(1000)` is how
  MicroPython servo drivers start.
- **machine**: `SPI` and `I2C` take `sck=`/`mosi=`/`miso=` and `scl=`/`sda=` naming the
  fixed hardware pins, instead of refusing any keyword pin argument; any other pin is
  refused by name.
- **machine**: `UART` takes upstream's `bits=`/`parity=`/`stop=`, and `write()`/`read()`/
  `readinto()`/`init()`/`deinit()`/`flush()` now compile and follow upstream's timeout
  semantics (`readinto` used to block until the buffer was full instead of returning what
  arrived within `timeout`/`timeout_char`) (PyMCU#451, #16).
- **machine**: `readfrom_mem`, `readfrom` and `SPI.read` take upstream's signatures
  (`readfrom_mem(addr, memaddr, nbytes)` returning a fresh buffer, not a four-argument
  caller-buffer extension).
- **machine**: `Signal` builds its `Pin` from either upstream constructor shape
  (`Signal(pin_obj, invert=)` or `Signal(pin_arguments..., invert=)`); the two-shape call
  used to bind the wrong form and fail to compile.
- **machine**: `disable_irq()`/`enable_irq(state)` go through the HAL's
  `save_and_disable_interrupts()`/`restore_interrupts()`. `disable_irq()` used to always
  return `1`, so a nested `enable_irq()` re-enabled interrupts the outer section still
  held disabled (PyMCU#353), a silent-wrong-value bug now closed.
- **machine**: `ADC.read_u16()` reaches `65535` at full scale (10-bit reading was linearly
  scaled by 64, topping out at `65472`); now bit-replicated like the rp2 port
  (`raw << 6 | raw >> 4`), a silent-wrong-value bug now closed.

## 0.1.0b1 (re-frozen from main, 2026-09-26)

This layer was out of scope for the 2026-09-15 freeze. It publishes in beta 1
after all, because what landed since then is not polish: a UART asking for
115200 was getting 50000, a byte count could not hold a buffer past 255, and
`framebuf` did not exist. The `pymcu-stdlib` floor moved with it, from
`0.1.0a10` to `0.1.0b1`, since the module leans on compiler behaviour that
only b1 has.

### New

- **framebuf**: the module MicroPython keeps in C, re-expressed for this layer.
  `FrameBuffer(buffer, width, height, format[, stride])` and `FrameBuffer1` over a
  caller-owned `bytearray`, with `fill`, `fill_rect`, `pixel`, `hline`, `vline`, `rect`,
  `line`, `ellipse`, `text`, `scroll` and `blit` in MONO_VLSB, MONO_HLSB, MONO_HMSB,
  GS2_HMSB, GS4_HMSB, GS8 and RGB565. What it draws is pinned byte for byte against the
  real interpreter running the same programs (`tests/test_framebuf.py`), and the same
  probes are run as compiled AVR firmware on the emulated Uno in the `pymcu-avr` checkout.
  A format that is a compile-time constant, which is what every driver passes, folds the
  format ladder away and the unused arms cost nothing. The buffer is checked against the
  geometry while compiling, with upstream's own formula, so a buffer too small for its
  width, height and format is refused instead of being written past its end; agreed with
  the real interpreter over 210 boundary cases. `poly()`, a run-time text string and
  the tuple form of `blit()`'s source are refused with diagnostics that name the
  alternative, and `ellipse()` is refused too while PyMCU/PyMCU#510 is
  open: it is implemented and correct, but a program whose only call to it is one call gets
  it inlined and the inlined filled walk writes the wrong pixels without saying so. See `docs/limitations.md`.

### Fixed

- **machine**: `I2C` and `SoftI2C` `writeto`, `readfrom`, `readfrom_into`,
  `writeto_mem`, `readfrom_mem` and `readfrom_mem_into` ignored the bus's return status,
  so a NACKed transaction looked like a successful one. They now raise
  `OSError("[Errno 5] EIO")`, the message the MicroPython ports print, after stopping
  the bus. The mock buses grow `nack` / `fail_start` knobs so a test can drive each
  failure.

## 0.1.0a2 — 2026-08-18

Driven by compiling the official MicroPython quickref examples verbatim
against the layer. New surface is silicon-verified on an Arduino Uno.

### New
- `machine.ADC(0)`..`ADC(5)`: ESP-style channel numbers map to A0-A5,
  alongside the existing `ADC(Pin(14))` form.
- `machine.PWM.freq()` and `duty_u16()` getters (MicroPython reads both
  back). They return the last requested value; the timer runs at the
  nearest achievable prescaler bucket.
- `machine.SoftI2C(scl=Pin(9), sda=Pin(8), freq=100000)` over the HAL
  bit-bang controller: scan, writeto, readfrom on any two pins.

### Honest diagnostics (were arity errors or silence)
- `machine.unique_id()`: the ATmega328P has no unique hardware ID; the
  error names the EEPROM alternative.
- `machine.UART.readline()` with no args needs a heap-allocated return;
  the error shows the `readline(buf)` form.

### Fixed
- Pin mapping is arch-dispatched with strict argument checking: an
  invalid pin number or a runtime-varying `Pin()` argument is a located
  compile error instead of silently driving a fixed pin.

### Requires
- pymcu-compiler >= 0.1.0a10 (getter/setter overloads on ZCA fields,
  channel-form overload resolution, const float parameters).
