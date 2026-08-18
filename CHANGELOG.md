# Changelog — pymcu-micropython

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
