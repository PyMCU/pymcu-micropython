"""Each machine class compiles on rp2040, or fails there with the chip's own error.

These build small programs with the real compiler, so they need `pymcu` on PATH or in
PYMCU_BIN. The CPython tests in this directory cannot see a missing HAL; this one can.

A class whose HAL the chip has must resolve its HAL name (no "undefined function"). A class
whose HAL the chip does not have must stop with "machine.<Class> is not available on <chip>
yet", at the caller's line.
"""
import os
import re
import shutil
import subprocess
from pathlib import Path

import pytest

PYMCU = os.environ.get("PYMCU_BIN") or shutil.which("pymcu")
pytestmark = pytest.mark.skipif(not PYMCU, reason="no pymcu driver: put pymcu on PATH or set PYMCU_BIN")

BOARDS = {
    "rp2040": ("raspberry_pi_pico", 125000000),
    "avr": ("arduino_uno", 16000000),
}

PYPROJECT = """[project]
name = "hal-probe"
version = "0.1.0"
requires-python = ">=3.11"

[tool.pymcu]
board     = "{board}"
frequency = {freq}
sources   = "src"
entry     = "main.py"
stdlib    = ["micropython"]
"""


def _build(tmp_path: Path, src: str, chip: str) -> tuple[int, str]:
    board, freq = BOARDS[chip]
    (tmp_path / "src").mkdir()
    (tmp_path / "src" / "main.py").write_text(src)
    (tmp_path / "pyproject.toml").write_text(PYPROJECT.format(board=board, freq=freq))
    result = subprocess.run([PYMCU, "build"], cwd=tmp_path, capture_output=True, text=True, timeout=600)
    return result.returncode, result.stdout + result.stderr


def _resolves(log: str, name: str) -> bool:
    return not re.search(rf"undefined function '{re.escape(name)}'", log)


def test_adc_resolves_its_hal_on_rp2040(tmp_path):
    rc, log = _build(tmp_path, 'from machine import ADC\na = ADC(0)\nprint("END")\n', "rp2040")
    assert "undefined function" not in log, log


def test_pwm_resolves_its_hal_on_rp2040(tmp_path):
    rc, log = _build(tmp_path, 'from machine import PWM, Pin\np = PWM(Pin(16))\nprint("END")\n', "rp2040")
    assert "undefined function" not in log, log


def test_i2c_resolves_its_hal_on_rp2040(tmp_path):
    rc, log = _build(tmp_path, 'from machine import I2C\ni = I2C(0)\nprint("END")\n', "rp2040")
    assert "undefined function" not in log, log


def test_spi_resolves_its_hal_on_rp2040(tmp_path):
    rc, log = _build(tmp_path, 'from machine import SPI\ns = SPI(0)\nprint("END")\n', "rp2040")
    assert "undefined function" not in log, log


def test_wdt_on_rp2040_is_a_clear_error_at_the_caller(tmp_path):
    rc, log = _build(tmp_path, 'from machine import WDT\nw = WDT(timeout=2000)\nw.feed()\nprint("END")\n', "rp2040")
    assert rc != 0, log
    assert "machine.WDT is not available on rp2040 yet" in log, log
    assert "src/main.py:2:" in log, log
    assert "undefined function" not in log, log


def test_timer_on_rp2040_is_a_clear_error_at_the_caller(tmp_path):
    rc, log = _build(tmp_path, 'from machine import Timer\nt = Timer(0)\nprint("END")\n', "rp2040")
    assert rc != 0, log
    assert "machine.Timer is not available on rp2040 yet" in log, log
    assert "src/main.py:2:" in log, log
    assert "undefined function" not in log, log


def test_wdt_compiles_on_avr(tmp_path):
    rc, log = _build(tmp_path, 'from machine import WDT\nw = WDT(timeout=2000)\nw.feed()\nprint("END")\n', "avr")
    assert rc == 0, log


def test_timer_compiles_on_avr(tmp_path):
    rc, log = _build(tmp_path, 'from machine import Timer\nt = Timer(0)\nprint("END")\n', "avr")
    assert rc == 0, log
