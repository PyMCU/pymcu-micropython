# Changelog — pymcu-micropython

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
