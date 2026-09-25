"""
The buffer-size check against the interpreter's own rule.

Upstream refuses a buffer too small for the geometry with a `ValueError` from
`framebuf_make_new_helper`. There is no heap here to raise one, and on a
microcontroller the alternative is not an exception that never arrives, it is
writing past the end of somebody else's SRAM. So the same refusal is made while
the sizes are still constants, which in the shape people write is exactly when
they are.

The table below is upstream's formula, rounding included, recomputed here
independently of the module so a change to either side shows up. Each geometry
is tried one byte under, exactly at, and one byte over the requirement. The
same 210 cases were run against the real interpreter (unix port) and against
compiled AVR firmware: the three agree, except for buffers past 2 KB which the
AVR backend refuses first for not fitting in SRAM.
"""
from __future__ import annotations

import pytest
from pymcu.exceptions import CompileError

import pymcu_micropython.framebuf as framebuf

MONO_VLSB, RGB565, GS4_HMSB, MONO_HLSB, MONO_HMSB, GS2_HMSB, GS8 = 0, 1, 2, 3, 4, 5, 6

FORMATS = [
    ("MONO_VLSB", MONO_VLSB),
    ("MONO_HLSB", MONO_HLSB),
    ("MONO_HMSB", MONO_HMSB),
    ("GS2_HMSB", GS2_HMSB),
    ("GS4_HMSB", GS4_HMSB),
    ("GS8", GS8),
    ("RGB565", RGB565),
]
GEOMETRIES = [(64, 32), (64, 20), (30, 16), (17, 9), (8, 8)]


def required_bytes(fmt: int, width: int, height: int, stride: int | None) -> int:
    """extmod/modframebuf.c, framebuf_make_new_helper."""
    bpp = 1
    height_required = height
    width_required = width
    strides_required = height - 1
    st = width if stride is None else stride
    if fmt == MONO_VLSB:
        height_required = (height + 7) & ~7
        strides_required = height_required - 8
    elif fmt in (MONO_HLSB, MONO_HMSB):
        st = (st + 7) & ~7
        width_required = (width + 7) & ~7
    elif fmt == GS2_HMSB:
        st = (st + 3) & ~3
        width_required = (width + 3) & ~3
        bpp = 2
    elif fmt == GS4_HMSB:
        st = (st + 1) & ~1
        width_required = (width + 1) & ~1
        bpp = 4
    elif fmt == GS8:
        bpp = 8
    elif fmt == RGB565:
        bpp = 16
    return (strides_required * st + (height_required - strides_required) * width_required) * bpp // 8


def _build(fmt: int, width: int, height: int, stride: int | None, length: int):
    buf = bytearray(length)
    if stride is None:
        return framebuf.FrameBuffer(buf, width, height, fmt)
    return framebuf.FrameBuffer(buf, width, height, fmt, stride)


CASES = [
    (name, fmt, w, h, stride)
    for name, fmt in FORMATS
    for (w, h) in GEOMETRIES
    for stride in (None, w + 5)
]
IDS = [f"{n}-{w}x{h}-stride{s}" for (n, _, w, h, s) in CASES]


@pytest.mark.parametrize(("name", "fmt", "width", "height", "stride"), CASES, ids=IDS)
def test_exact_buffer_is_accepted(name, fmt, width, height, stride) -> None:
    need = required_bytes(fmt, width, height, stride)
    fb = _build(fmt, width, height, stride, need)
    assert fb.width == width and fb.height == height


@pytest.mark.parametrize(("name", "fmt", "width", "height", "stride"), CASES, ids=IDS)
def test_one_byte_short_is_refused(name, fmt, width, height, stride) -> None:
    need = required_bytes(fmt, width, height, stride)
    with pytest.raises(CompileError) as excinfo:
        _build(fmt, width, height, stride, need - 1)
    assert "too small for the geometry" in str(excinfo.value)


@pytest.mark.parametrize(("name", "fmt", "width", "height", "stride"), CASES, ids=IDS)
def test_one_byte_over_is_accepted(name, fmt, width, height, stride) -> None:
    need = required_bytes(fmt, width, height, stride)
    assert _build(fmt, width, height, stride, need + 1) is not None


def test_the_shape_people_write() -> None:
    buf = bytearray(256)
    assert framebuf.FrameBuffer(buf, 64, 32, MONO_VLSB) is not None
    with pytest.raises(CompileError):
        framebuf.FrameBuffer(bytearray(255), 64, 32, MONO_VLSB)
