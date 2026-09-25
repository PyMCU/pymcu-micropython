"""
framebuf drawing fidelity against MicroPython's own builtin module.

framebuf is written in C inside the interpreter (extmod/modframebuf.c), so
there is no upstream Python source to compare this layer's implementation
against line by line. What can be compared is what it draws: each probe under
tests/framebuf/probes/ fills a buffer with the whole primitive surface and
prints every byte of it, and the file of the same name under
tests/framebuf/expected/ is what MicroPython's builtin printed for that exact
program (unix port, v1.29.0-preview, extmod/modframebuf.c at 9f396bba8d).

Regenerate an expected file only after checking the change against the real
interpreter:

    micropython tests/framebuf/probes/<name>.py > tests/framebuf/expected/<name>.txt

The same probes are run as compiled AVR firmware on the emulated Uno in the
pymcu-avr checkout; the three outputs are byte for byte the same.
"""
from __future__ import annotations

import io
import sys
from contextlib import redirect_stdout
from pathlib import Path

import pytest

import pymcu_micropython.framebuf as framebuf_module

PROBES = sorted((Path(__file__).parent / "framebuf" / "probes").glob("*.py"))
EXPECTED = Path(__file__).parent / "framebuf" / "expected"


def _run(source: Path) -> str:
    previous = sys.modules.get("framebuf")
    sys.modules["framebuf"] = framebuf_module
    try:
        out = io.StringIO()
        namespace: dict[str, object] = {"__name__": "__main__"}
        with redirect_stdout(out):
            exec(compile(source.read_text(), str(source), "exec"), namespace)
        return out.getvalue()
    finally:
        if previous is None:
            del sys.modules["framebuf"]
        else:
            sys.modules["framebuf"] = previous


@pytest.mark.parametrize("probe", PROBES, ids=lambda p: p.stem)
def test_draws_what_micropython_draws(probe: Path) -> None:
    expected = (EXPECTED / f"{probe.stem}.txt").read_text()
    produced = _run(probe)
    if produced == expected:
        return
    got = produced.splitlines()
    want = expected.splitlines()
    for index, (a, b) in enumerate(zip(want, got)):
        if a != b:
            pytest.fail(
                f"{probe.stem}: line {index + 1} is {b!r}, MicroPython prints {a!r}"
            )
    pytest.fail(
        f"{probe.stem}: MicroPython prints {len(want)} lines, this prints {len(got)}"
    )


def test_every_probe_has_an_expected_file() -> None:
    assert PROBES, "no framebuf probes found"
    missing = [p.stem for p in PROBES if not (EXPECTED / f"{p.stem}.txt").is_file()]
    assert not missing, f"probes with no MicroPython reference: {missing}"
