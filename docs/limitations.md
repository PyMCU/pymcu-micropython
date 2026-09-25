# API limitations

This layer targets AVR microcontrollers (Arduino Uno and other ATmega/ATtiny boards). Some
symbols in `micropython-rp2-stubs` (the parity suite's reference, `tests/parity/`) describe
hardware, a runtime, or a MicroPython stub-authoring convention that does not apply to this
class of chip. Each section below is quoted by `tests/parity/allowlist.toml` for the symbols
it covers.

## network

`network` is not implemented: this class of AVR chip has no radio hardware, so `network.WLAN`,
`network.LAN`, `network.PPP` and the module-level network helpers and constants have nothing to
control.

## rp2

`rp2` targets the RP2040/RP2350 PIO state machines and DMA channels, neither of which exists on
this class of AVR chip, so `rp2.PIO`, `rp2.StateMachine`, `rp2.DMA` and the module-level `rp2`
helpers are not implemented.

## framebuf

`framebuf` is a builtin of the MicroPython interpreter, written in C
(`extmod/modframebuf.c`), so there is no upstream Python source to vendor: this layer
re-expresses that C module. What it draws is pinned against the real interpreter, probe by
probe, in `tests/test_framebuf.py`: MONO_VLSB, MONO_HLSB, MONO_HMSB, GS2_HMSB, GS4_HMSB,
GS8 and RGB565, with the clipping, the per-format stride rounding and the out-of-bounds
answers. The buffer stays the caller's, as upstream: a `FrameBuffer` never allocates.

`FrameBuffer.text()` takes a string known at compile time. Upstream walks the characters of
any string at run time; the compiler has no run-time string iteration, so the walk is
unrolled while compiling. A string that differs between paths is refused, naming the loop,
instead of drawing something else.

`FrameBuffer.ellipse()` is refused while PyMCU/PyMCU#510 is open, and the refusal says so. The walk is
implemented and draws what the interpreter draws -- under CPython, and on the board
whenever the program calls `ellipse()` from more than one place. With a single call site
the compiler inlines the method instead of emitting it as a subroutine, and the inlined
filled walk writes different pixels: 11 bytes of 256 for
`ellipse(30, 15, 10, 8, 1, True)` on a 64x32 MONO_VLSB buffer, with nothing said. The
other ten primitives were each measured with a single call site and are correct. Drawing
almost the right ellipse in silence is worse than refusing, so this refuses until the
inliner is fixed, and the diagnostic names the issue and the workaround;
`tests/framebuf/withheld/` keeps the probe and the interpreter's output
for the day it is lifted.

`FrameBuffer.poly()` is refused with a diagnostic. Its outline walk indexes an array of
coordinates at run time and its filled walk needs one array of scan-line crossings per
polygon, sized at run time, and there is no heap to size it in. `FrameBuffer.line()` draws
the edges.

`FrameBuffer.blit()` takes a `FrameBuffer`, never the `(buffer, width, height, format[,
stride])` tuple upstream also accepts as the source.

The constructor refuses at compile time what upstream refuses with a `ValueError` at run
time: a width or height below 1, a stride below width, an unknown format. Raising needs a
heap, so the check has to happen while the sizes are still constants. It does **not** check
the buffer against the geometry the way upstream does, because `len()` of a `bytearray`
parameter has no lowering: a buffer too small for its width, height and format is written
past its end.

Every index is computed in 16 bits, so the addressable buffer stops at 32767 bytes. That
covers every mono display and every small colour one; a 320x240 RGB565 frame is past it.

`FrameBuffer1` is a subclass of `FrameBuffer` here and a factory function upstream, so
`type()` answers differently and nothing that draws does.

Every drawing method is positional-only upstream. A `/` in a `def` is syntax the compiler
refuses, so the whole surface differs from the stub by that marker and by nothing else:
the parameter names, their order and their defaults all match. Tracked by
PyMCU/pymcu-micropython#19, the same gap as `machine.Pin.irq`.

## machine.ADC attenuation and resolution

`machine.ADC`'s attenuation (`ATTN_*`) and resolution (`WIDTH_*`) controls, its `CORE_TEMP`,
`CORE_VBAT` and `CORE_VREF` internal channels, and `ADCBlock`/`ADCWiPy` are ESP32 and Pycom
WiPy specific; this chip's ADC has one fixed input range and a fixed 10-bit resolution, so none
of them apply.

## machine constants and methods the stub declares but the firmware does not

`machine.IDLE`, `SLEEP`, `DEEPSLEEP`, `HARD_RESET`, `SOFT_RESET`, `DEEPSLEEP_RESET`,
`PIN_WAKE`, `RTC_WAKE`, `WLAN_WAKE` and `machine.SPI.CONTROLLER` appear in the rp2
stub but not in the rp2 firmware's `machine` module, measured on MicroPython 1.21
on real RP2040 silicon: they are esp32-port names the stub carries over. This
layer matches the firmware, not the stub, so the only reset-cause constants are
`PWRON_RESET` (1) and `WDT_RESET` (3). `machine.Pin.mode`, `Pin.pull`,
`Pin.drive`, `machine.I2C.deinit`, `machine.SoftI2C.deinit` and
`machine.ADC.read` are the same
story: the stub carries them from ports that keep separate mode/pull/drive
accessors or a bus teardown method, while the rp2 firmware re-initialises a pin
through `Pin.init(mode=..., pull=..., drive=...)`, defines none of them, and
reads its ADC only through `ADC.read_u16()`.

## machine.Pin alternate functions and drive strength

`machine.Pin`'s `ALT_*` function-select constants, `DRIVE_0`/`DRIVE_1`/`DRIVE_2`, `drive`,
`ANALOG`, `PULL_HOLD`, `IRQ_HIGH_LEVEL` and `IRQ_LOW_LEVEL` describe the RP2040's
per-pin function multiplexer, programmable drive-strength register and level-triggered IRQ
modes; this chip's GPIO pins are fixed-function with a fixed drive strength and only
edge-triggered external interrupts, so none of them apply. `Pin.OPEN_DRAIN` keeps its
upstream value (2) because the name exists upstream, but selecting the mode is refused on
this chip -- the AVR GPIO block has no open-drain output configuration.

## Peripherals this chip does not have

`machine.I2S`, `machine.RTC`, `machine.SDCard` and `machine.USBDevice` are not implemented:
this chip has no I2S audio peripheral, no real-time-clock block, no SD/SDIO controller and no
USB device controller. `machine.mem32` is not implemented either: this is an 8-bit architecture
with a 16-bit address bus, and `mem8`/`mem16` already reach everything a `mem32` window would.
`machine.mem_backup` and `machine.bootloader` are not implemented: there is no always-on backup
memory domain and no software-triggered bootloader entry point on this chip.

## machine.UART flow control and idle/break detection

`machine.UART`'s `CTS`, `RTS`, `IDLE`, `INV_RX`, `INV_TX`, `IRQ_BREAK`, `IRQ_RX`, `IRQ_RXIDLE`
and `IRQ_TXIDLE` are not implemented: this chip's USART has no hardware flow-control pins and
this HAL does not expose a break-detect or RX-idle-timeout interrupt source.

## micropython runtime introspection

`micropython.mem_info`, `qstr_info`, `stack_use`, `heap_lock`, `heap_unlock`, `opt_level`,
`kbd_intr`, `alloc_emergency_exception_buf`, `RingIO` and `Const_T` describe MicroPython's
bytecode interpreter and its heap and interned-string table; PyMCU compiles ahead of time to
native code with no interpreter, heap or qstr table at runtime, so there is nothing for them to
report on. `micropython.asm_thumb` and `micropython.asm_xtensa` are inline assemblers for
architectures this compiler does not target.

## time and utime calendar functions

`time.gmtime`, `localtime`, `mktime`, `time` and `time_ns` (and their `utime` aliases) need a
real-time clock to track wall-clock time across resets; this chip has no RTC peripheral, so
only the free-running `ticks_ms()`/`ticks_us()` counters are available.

## machine.PWM.init's stub defaults

MicroPython's own stub file marks `PWM.init()`'s `freq`, `duty_u16`, `duty_ns` and `invert`
keyword defaults as `...` (implementation-defined); this layer's concrete `0` defaults are the
actual values applied when a keyword is omitted.

## Reading a variable amount of data with no heap

`machine.I2C.readfrom_mem(addr, memaddr, nbytes)` returns a freshly-allocated `bytes` object
of `nbytes`; this chip has no heap to allocate one from, so this layer's `readfrom_mem(addr,
memaddr, buf, n)` takes a caller-owned buffer and a count instead, the same deviation
`machine.SPI.read(nbytes)` and `machine.UART.readline()`'s no-argument form already carry (see
their own docstrings) -- `readfrom_mem_into(addr, memaddr, buf)`, `SPI.readinto(buf)` and
`UART.readline(buf)` are the faithful, buffer-based equivalents.
