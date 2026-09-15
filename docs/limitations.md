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

## machine.ADC attenuation and resolution

`machine.ADC`'s attenuation (`ATTN_*`) and resolution (`WIDTH_*`) controls, its `CORE_TEMP`,
`CORE_VBAT` and `CORE_VREF` internal channels, and `ADCBlock`/`ADCWiPy` are ESP32 and Pycom
WiPy specific; this chip's ADC has one fixed input range and a fixed 10-bit resolution, so none
of them apply.

## machine.Pin alternate functions and drive strength

`machine.Pin`'s `ALT_*` function-select constants, `DRIVE_0`/`DRIVE_1`/`DRIVE_2`, `drive`,
`ANALOG`, `OPEN_DRAIN`, `PULL_HOLD`, `IRQ_HIGH_LEVEL` and `IRQ_LOW_LEVEL` describe the RP2040's
per-pin function multiplexer, programmable drive-strength register and level-triggered IRQ
modes; this chip's GPIO pins are fixed-function with a fixed drive strength and only
edge-triggered external interrupts, so none of them apply.

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
