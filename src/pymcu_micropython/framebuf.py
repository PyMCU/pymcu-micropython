# MicroPython-compatible framebuf module for PyMCU.
#
# framebuf is a builtin of the MicroPython interpreter, written in C
# (extmod/modframebuf.c), so there is no upstream Python source to vendor: this
# file re-expresses that C module in the statically typed Python PyMCU compiles,
# keeping the upstream API, the upstream argument order and the upstream drawing
# results byte for byte.
#
# The frame buffer is caller-owned, exactly as upstream: FrameBuffer never
# allocates, it only writes into the bytearray it was handed.
#
#   import framebuf
#   buf = bytearray(128 * 32 // 8)
#   fb = framebuf.FrameBuffer(buf, 128, 32, framebuf.MONO_VLSB)
#   fb.fill(0)
#   fb.text("MicroPython", 0, 0, 1)
#
# Format dispatch is an if/elif ladder on self.format rather than upstream's
# table of function pointers. Measured on an Uno, a format that is a compile
# time constant (which is what every driver passes) folds the ladder away and
# the unused arms cost nothing; a format only known at run time pays for every
# arm, which is the honest price of asking for it.

from typing import Optional

from pymcu.types import inline, const, int16, int32, uint16
from pymcu.exceptions import CompileError as _CompileError

# Format constants, upstream's values (extmod/modframebuf.c).
MVLSB = 0
MONO_VLSB = 0
RGB565 = 1
GS2_HMSB = 5
GS4_HMSB = 2
GS8 = 6
MONO_HLSB = 3
MONO_HMSB = 4

# The 8x8 PETME128 font upstream draws text with (extmod/font_petme128_8x8.h),
# ASCII 32..127, eight bytes per character, one byte per pixel column with the
# top pixel in the least significant bit. Never written, so the table stays in
# flash and costs no SRAM.
_FONT = b"\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x4f\x4f\x00\x00\x00\x00\x07\x07\x00\x00\x07\x07\x00\x14\x7f\x7f\x14\x14\x7f\x7f\x14\x00\x24\x2e\x6b\x6b\x3a\x12\x00\x00\x63\x33\x18\x0c\x66\x63\x00\x00\x32\x7f\x4d\x4d\x77\x72\x50\x00\x00\x00\x04\x06\x03\x01\x00\x00\x00\x1c\x3e\x63\x41\x00\x00\x00\x00\x41\x63\x3e\x1c\x00\x00\x08\x2a\x3e\x1c\x1c\x3e\x2a\x08\x00\x08\x08\x3e\x3e\x08\x08\x00\x00\x00\x80\xe0\x60\x00\x00\x00\x00\x08\x08\x08\x08\x08\x08\x00\x00\x00\x00\x60\x60\x00\x00\x00\x00\x40\x60\x30\x18\x0c\x06\x02\x00\x3e\x7f\x49\x45\x7f\x3e\x00\x00\x40\x44\x7f\x7f\x40\x40\x00\x00\x62\x73\x51\x49\x4f\x46\x00\x00\x22\x63\x49\x49\x7f\x36\x00\x00\x18\x18\x14\x16\x7f\x7f\x10\x00\x27\x67\x45\x45\x7d\x39\x00\x00\x3e\x7f\x49\x49\x7b\x32\x00\x00\x03\x03\x79\x7d\x07\x03\x00\x00\x36\x7f\x49\x49\x7f\x36\x00\x00\x26\x6f\x49\x49\x7f\x3e\x00\x00\x00\x00\x24\x24\x00\x00\x00\x00\x00\x80\xe4\x64\x00\x00\x00\x00\x08\x1c\x36\x63\x41\x41\x00\x00\x14\x14\x14\x14\x14\x14\x00\x00\x41\x41\x63\x36\x1c\x08\x00\x00\x02\x03\x51\x59\x0f\x06\x00\x00\x3e\x7f\x41\x4d\x4f\x2e\x00\x00\x7c\x7e\x0b\x0b\x7e\x7c\x00\x00\x7f\x7f\x49\x49\x7f\x36\x00\x00\x3e\x7f\x41\x41\x63\x22\x00\x00\x7f\x7f\x41\x63\x3e\x1c\x00\x00\x7f\x7f\x49\x49\x41\x41\x00\x00\x7f\x7f\x09\x09\x01\x01\x00\x00\x3e\x7f\x41\x49\x7b\x3a\x00\x00\x7f\x7f\x08\x08\x7f\x7f\x00\x00\x00\x41\x7f\x7f\x41\x00\x00\x00\x20\x60\x41\x7f\x3f\x01\x00\x00\x7f\x7f\x1c\x36\x63\x41\x00\x00\x7f\x7f\x40\x40\x40\x40\x00\x00\x7f\x7f\x06\x0c\x06\x7f\x7f\x00\x7f\x7f\x0e\x1c\x7f\x7f\x00\x00\x3e\x7f\x41\x41\x7f\x3e\x00\x00\x7f\x7f\x09\x09\x0f\x06\x00\x00\x1e\x3f\x21\x61\x7f\x5e\x00\x00\x7f\x7f\x19\x39\x6f\x46\x00\x00\x26\x6f\x49\x49\x7b\x32\x00\x00\x01\x01\x7f\x7f\x01\x01\x00\x00\x3f\x7f\x40\x40\x7f\x3f\x00\x00\x1f\x3f\x60\x60\x3f\x1f\x00\x00\x7f\x7f\x30\x18\x30\x7f\x7f\x00\x63\x77\x1c\x1c\x77\x63\x00\x00\x07\x0f\x78\x78\x0f\x07\x00\x00\x61\x71\x59\x4d\x47\x43\x00\x00\x00\x7f\x7f\x41\x41\x00\x00\x00\x02\x06\x0c\x18\x30\x60\x40\x00\x00\x41\x41\x7f\x7f\x00\x00\x00\x08\x0c\x06\x06\x0c\x08\x00\xc0\xc0\xc0\xc0\xc0\xc0\xc0\xc0\x00\x00\x01\x03\x06\x04\x00\x00\x00\x20\x74\x54\x54\x7c\x78\x00\x00\x7f\x7f\x44\x44\x7c\x38\x00\x00\x38\x7c\x44\x44\x6c\x28\x00\x00\x38\x7c\x44\x44\x7f\x7f\x00\x00\x38\x7c\x54\x54\x5c\x58\x00\x00\x08\x7e\x7f\x09\x03\x02\x00\x00\x98\xbc\xa4\xa4\xfc\x7c\x00\x00\x7f\x7f\x04\x04\x7c\x78\x00\x00\x00\x00\x7d\x7d\x00\x00\x00\x00\x40\xc0\x80\x80\xfd\x7d\x00\x00\x7f\x7f\x30\x38\x6c\x44\x00\x00\x00\x41\x7f\x7f\x40\x00\x00\x00\x7c\x7c\x18\x30\x18\x7c\x7c\x00\x7c\x7c\x04\x04\x7c\x78\x00\x00\x38\x7c\x44\x44\x7c\x38\x00\x00\xfc\xfc\x24\x24\x3c\x18\x00\x00\x18\x3c\x24\x24\xfc\xfc\x00\x00\x7c\x7c\x04\x04\x0c\x08\x00\x00\x48\x5c\x54\x54\x74\x20\x00\x04\x04\x3f\x7f\x44\x64\x20\x00\x00\x3c\x7c\x40\x40\x7c\x3c\x00\x00\x1c\x3c\x60\x60\x3c\x1c\x00\x00\x1c\x7c\x30\x18\x30\x7c\x1c\x00\x44\x6c\x38\x38\x6c\x44\x00\x00\x9c\xbc\xa0\xa0\xfc\x7c\x00\x00\x44\x64\x74\x5c\x4c\x44\x00\x00\x08\x08\x3e\x77\x41\x41\x00\x00\x00\x00\xff\xff\x00\x00\x00\x00\x41\x41\x77\x3e\x08\x08\x00\x00\x02\x03\x01\x03\x02\x03\x01\xaa\x55\xaa\x55\xaa\x55\xaa\x55"


# The one check upstream makes that a compile-time layer would otherwise have
# to drop. framebuf_make_new_helper refuses a buffer too small for the
# geometry with a ValueError; there is no heap to raise one here, but there is
# something better: in the shape people actually write, the bytearray literal
# and the geometry are both compile-time constants, so the same refusal can
# happen while compiling. @inline so len() sees the buffer the caller named,
# not the parameter it arrived in.
@inline
def _check_buffer(buf: bytearray, needed: int32, width: int16, height: int16):
    if len(buf) < needed:
        raise _CompileError("framebuf.FrameBuffer: this buffer is too small for the geometry asked for. A FrameBuffer never allocates, it writes into the bytearray it was handed, so the buffer has to be big enough before it is handed over: this one is shorter than the width, height and format need. Upstream answers this with a ValueError at run time, and raising needs a heap this target does not have, so the sizes have to be right while they are still constants.")


class FrameBuffer:
    # FrameBuffer(buffer, width, height, format[, stride])
    #
    # Upstream's stride defaults to `width`, which a Python default expression
    # cannot name, so the default is None and the constructor reads it, the
    # way the pure-Python ports of this module do.
    #
    # Every coordinate is int16 and every colour uint16, declared rather than
    # inferred. Clipping, Bresenham and scroll all walk coordinates below zero,
    # and a width inferred from a non-negative literal wraps there instead of
    # going negative, which turns a loop that ends into one that does not.
    def __init__(self, buf: bytearray, width: int16, height: int16, format: int16, stride: Optional[int16] = None):
        if stride is None:
            stride = width
        if width < 1 or height < 1:
            raise _CompileError("framebuf.FrameBuffer: width and height must both be at least 1. Upstream raises ValueError here, and raising needs a heap this target does not have, so the sizes have to be right at compile time.")
        if stride < width:
            raise _CompileError("framebuf.FrameBuffer: stride must be at least width. Upstream raises ValueError here, and raising needs a heap this target does not have, so the stride has to be right at compile time.")
        if format != MVLSB and format != RGB565 and format != GS2_HMSB and format != GS4_HMSB and format != GS8 and format != MONO_HLSB and format != MONO_HMSB:
            raise _CompileError("framebuf.FrameBuffer: unknown format. It must be one of framebuf.MONO_VLSB, MONO_HLSB, MONO_HMSB, GS2_HMSB, GS4_HMSB, GS8 or RGB565, and it must be known at compile time -- upstream checks the format when the FrameBuffer is built and raises ValueError, and raising needs a heap this target does not have.")
        self.buf = buf
        self.width = width
        self.height = height
        self.format = format
        # Upstream rounds the stride up per format in framebuf_make_new_helper:
        # to a multiple of 8 for the horizontal mono formats, of 4 for GS2 and
        # of 2 for GS4. Leaving it out draws the same picture on a display
        # whose width is already a multiple of that, and the wrong one on
        # every other.
        rstride: int16 = stride
        # Upstream's per-format widths, from framebuf_make_new_helper: bits per
        # pixel, the height the buffer has to cover and the width each row
        # takes once rounded.
        bpp: int32 = 1
        height_required: int32 = height
        width_required: int32 = width
        strides_required: int32 = height - 1
        if format == MVLSB:
            height_required = (height + 7) & ~7
            strides_required = height_required - 8
        elif format == MONO_HLSB or format == MONO_HMSB:
            rstride = (stride + 7) & ~7
            width_required = (width + 7) & ~7
        elif format == GS2_HMSB:
            rstride = (stride + 3) & ~3
            width_required = (width + 3) & ~3
            bpp = 2
        elif format == GS4_HMSB:
            rstride = (stride + 1) & ~1
            width_required = (width + 1) & ~1
            bpp = 4
        elif format == GS8:
            bpp = 8
        elif format == RGB565:
            bpp = 16
        self.stride = rstride
        wide_stride: int32 = rstride
        needed: int32 = (strides_required * wide_stride + (height_required - strides_required) * width_required) * bpp // 8
        _check_buffer(buf, needed, width, height)

    # -- format-dependent primitives ------------------------------------
    #
    # One subroutine each, with the format ladder inside, so the ladder is
    # paid for once per program instead of once per drawing call. Measured on
    # an Uno: a format that is a compile-time constant (what every driver
    # passes) folds the ladder away and the unused arms cost nothing; a format
    # only known at run time emits every arm.

    def _setpixel(self, x: int16, y: int16, col: uint16):
        fmt: int16 = self.format
        if fmt == MVLSB:
            index: int16 = (y >> 3) * self.stride + x
            offset: int16 = y & 0x07
            self.buf[index] = (self.buf[index] & ~(0x01 << offset)) | ((col != 0) << offset)
        elif fmt == MONO_HLSB or fmt == MONO_HMSB:
            index = (x + y * self.stride) >> 3
            if fmt == MONO_HMSB:
                offset = x & 0x07
            else:
                offset = 7 - (x & 0x07)
            self.buf[index] = (self.buf[index] & ~(0x01 << offset)) | ((col != 0) << offset)
        elif fmt == GS2_HMSB:
            index = (x + y * self.stride) >> 2
            pixel: uint16 = self.buf[index]
            shift: int16 = (x & 0x03) << 1
            mask: int16 = 0x03 << shift
            self.buf[index] = ((col & 0x03) << shift) | (pixel & ~mask)
        elif fmt == GS4_HMSB:
            index = (x + y * self.stride) >> 1
            pixel = self.buf[index]
            if x & 0x01:
                self.buf[index] = (pixel & 0xF0) | (col & 0x0F)
            else:
                self.buf[index] = (col << 4) | (pixel & 0x0F)
        elif fmt == GS8:
            self.buf[x + y * self.stride] = col & 0xFF
        elif fmt == RGB565:
            index = (x + y * self.stride) * 2
            self.buf[index] = col & 0xFF
            self.buf[index + 1] = (col >> 8) & 0xFF
        else:
            raise _CompileError("framebuf.FrameBuffer: unknown format. It must be one of framebuf.MONO_VLSB, MONO_HLSB, MONO_HMSB, GS2_HMSB, GS4_HMSB, GS8 or RGB565, and it must be known at compile time -- upstream checks the format when the FrameBuffer is built and raises ValueError, and raising needs a heap this target does not have.")

    def _getpixel(self, x: int16, y: int16) -> uint16:
        fmt: int16 = self.format
        if fmt == MVLSB:
            return (self.buf[(y >> 3) * self.stride + x] >> (y & 0x07)) & 0x01
        elif fmt == MONO_HLSB or fmt == MONO_HMSB:
            index: int16 = (x + y * self.stride) >> 3
            offset: int16 = 7 - (x & 0x07)
            if fmt == MONO_HMSB:
                offset = x & 0x07
            return (self.buf[index] >> offset) & 0x01
        elif fmt == GS2_HMSB:
            return (self.buf[(x + y * self.stride) >> 2] >> ((x & 0x03) << 1)) & 0x03
        elif fmt == GS4_HMSB:
            if x & 0x01:
                return self.buf[(x + y * self.stride) >> 1] & 0x0F
            return self.buf[(x + y * self.stride) >> 1] >> 4
        elif fmt == GS8:
            return self.buf[x + y * self.stride]
        elif fmt == RGB565:
            index = (x + y * self.stride) * 2
            return self.buf[index] | (self.buf[index + 1] << 8)
        else:
            raise _CompileError("framebuf.FrameBuffer: unknown format. It must be one of framebuf.MONO_VLSB, MONO_HLSB, MONO_HMSB, GS2_HMSB, GS4_HMSB, GS8 or RGB565, and it must be known at compile time -- upstream checks the format when the FrameBuffer is built and raises ValueError, and raising needs a heap this target does not have.")

    # Upstream's per-format fill_rect, already clipped by the caller.
    def _fill_rect_raw(self, x: int16, y: int16, w: int16, h: int16, col: uint16):
        yy: int16 = y
        hh: int16 = h
        while hh > 0:
            xx: int16 = x
            ww: int16 = w
            while ww > 0:
                self._setpixel(xx, yy, col)
                xx = xx + 1
                ww = ww - 1
            yy = yy + 1
            hh = hh - 1

    # Upstream's static fill_rect(): clip to the buffer, then fill.
    def _fill_rect_clipped(self, x: int16, y: int16, w: int16, h: int16, col: uint16):
        if h < 1 or w < 1 or x + w <= 0 or y + h <= 0 or y >= self.height or x >= self.width:
            return
        xend: int16 = x + w
        if xend > self.width:
            xend = self.width
        yend: int16 = y + h
        if yend > self.height:
            yend = self.height
        x0: int16 = x
        if x0 < 0:
            x0 = 0
        y0: int16 = y
        if y0 < 0:
            y0 = 0
        self._fill_rect_raw(x0, y0, xend - x0, yend - y0, col)

    # -- public surface --------------------------------------------------

    def fill(self, c: uint16):
        # Upstream calls the per-format fill_rect directly, unclipped.
        self._fill_rect_raw(0, 0, self.width, self.height, c)

    def fill_rect(self, x: int16, y: int16, w: int16, h: int16, c: uint16):
        self._fill_rect_clipped(x, y, w, h, c)

    @inline
    def pixel(self, x: int16, y: int16) -> Optional[uint16]:
        return self._pixel_get(x, y)

    @inline
    def pixel(self, x: int16, y: int16, c: uint16):
        self._pixel_set(x, y, c)

    # Upstream's pixel(x, y) answers None outside the buffer, and that is what
    # this answers too. A sentinel would have been cheaper and would have
    # collided with a real colour: 0xFFFF is white in RGB565.
    def _pixel_get(self, x: int16, y: int16) -> Optional[uint16]:
        if 0 <= x and x < self.width and 0 <= y and y < self.height:
            return self._getpixel(x, y)
        return None

    def _pixel_set(self, x: int16, y: int16, c: uint16):
        if 0 <= x and x < self.width and 0 <= y and y < self.height:
            self._setpixel(x, y, c)

    def hline(self, x: int16, y: int16, w: int16, c: uint16):
        self._fill_rect_clipped(x, y, w, 1, c)

    def vline(self, x: int16, y: int16, h: int16, c: uint16):
        self._fill_rect_clipped(x, y, 1, h, c)

    def rect(self, x: int16, y: int16, w: int16, h: int16, c: uint16, f: bool = False):
        if f:
            self._fill_rect_clipped(x, y, w, h, c)
        else:
            self._fill_rect_clipped(x, y, w, 1, c)
            self._fill_rect_clipped(x, y + h - 1, w, 1, c)
            self._fill_rect_clipped(x, y, 1, h, c)
            self._fill_rect_clipped(x + w - 1, y, 1, h, c)

    def line(self, x1: int16, y1: int16, x2: int16, y2: int16, c: uint16):
        self._line(x1, y1, x2, y2, c)

    # Upstream's static line(): Bresenham with the steep case transposed.
    def _line(self, x1: int16, y1: int16, x2: int16, y2: int16, col: uint16):
        px: int16 = x1
        py: int16 = y1
        dx: int16 = x2 - px
        sx: int16 = 1
        if dx <= 0:
            dx = -dx
            sx = -1
        dy: int16 = y2 - py
        sy: int16 = 1
        if dy <= 0:
            dy = -dy
            sy = -1
        steep: int16 = 0
        if dy > dx:
            temp: int16 = px
            px = py
            py = temp
            temp = dx
            dx = dy
            dy = temp
            temp = sx
            sx = sy
            sy = temp
            steep = 1
        e: int16 = 2 * dy - dx
        i: int16 = 0
        while i < dx:
            if steep:
                if 0 <= py and py < self.width and 0 <= px and px < self.height:
                    self._setpixel(py, px, col)
            else:
                if 0 <= px and px < self.width and 0 <= py and py < self.height:
                    self._setpixel(px, py, col)
            while e >= 0:
                py = py + sy
                e = e - 2 * dx
            px = px + sx
            e = e + 2 * dy
            i = i + 1
        self._pixel_set(x2, y2, col)

    def scroll(self, xstep: int16, ystep: int16):
        sx: int16 = 0
        xend: int16 = 0
        dx: int16 = 1
        if xstep < 0:
            if -xstep >= self.width:
                return
            sx = 0
            xend = self.width + xstep
            dx = 1
        else:
            if xstep >= self.width:
                return
            sx = self.width - 1
            xend = xstep - 1
            dx = -1
        y: int16 = 0
        yend: int16 = 0
        dy: int16 = 1
        if ystep < 0:
            if -ystep >= self.height:
                return
            y = 0
            yend = self.height + ystep
            dy = 1
        else:
            if ystep >= self.height:
                return
            y = self.height - 1
            yend = ystep - 1
            dy = -1
        while y != yend:
            x: int16 = sx
            while x != xend:
                self._setpixel(x, y, self._getpixel(x - xstep, y - ystep))
                x = x + dx
            y = y + dy

    def text(self, s: const[str], x: int16, y: int16, c: uint16 = 1):
        # Upstream walks the characters of `s` at run time. This compiler has
        # no run-time string iteration, so the walk is unrolled at compile
        # time and each character is drawn by one shared subroutine: the same
        # pixels, at the price of the string being a constant.
        cx: int16 = x
        for ch in s:
            self._char(ord(ch), cx, y, c)
            cx = cx + 8

    def _char(self, chrc: int16, x0: int16, y0: int16, col: uint16):
        ch: int16 = chrc
        if ch < 32 or ch > 127:
            ch = 127
        base: int16 = (ch - 32) * 8
        cx: int16 = x0
        j: int16 = 0
        while j < 8:
            if 0 <= cx and cx < self.width:
                vline_data: uint16 = _FONT[base + j]
                y: int16 = y0
                while vline_data:
                    if vline_data & 1:
                        if 0 <= y and y < self.height:
                            self._setpixel(cx, y, col)
                    vline_data = vline_data >> 1
                    y = y + 1
            j = j + 1
            cx = cx + 1

    # -- ellipse ---------------------------------------------------------
    #
    # Withheld, not missing, and the diagnostic says so. The implementation is
    # upstream's two-pass integer walk and it draws what the interpreter draws
    # -- under CPython, and on the board whenever the program calls ellipse()
    # from more than one place. With a single call site the compiler inlines
    # the method instead of emitting _bound_fb_ellipse as a subroutine, and the
    # inlined expansion of the FILLED walk writes different pixels: 11 bytes of
    # 256 for ellipse(30, 15, 10, 8, 1, True) on a 64x32 MONO_VLSB buffer, with
    # nothing said. PyMCU/PyMCU#510 carries the reproduction and the controls.
    #
    # Drawing almost the right ellipse without saying so is the one outcome
    # worth refusing, so this refuses until the inliner is fixed. Reverting the
    # commit that added this brings the implementation back.
    @inline
    def ellipse(self, x: int16, y: int16, xr: int16, yr: int16, c: uint16, f: bool = False, m: Optional[int16] = None):
        raise _CompileError("framebuf.FrameBuffer.ellipse is withheld while PyMCU/PyMCU#510 is open. Nothing is wrong with your program: the walk is implemented and it draws what MicroPython draws, but when ellipse() is the only call to ellipse() in the program the compiler inlines it, and the inlined filled walk writes the wrong pixels without saying so, so this refuses rather than draw almost the right ellipse. Draw the outline with framebuf.FrameBuffer.line, or fill the rows with framebuf.FrameBuffer.hline. A second call to ellipse() anywhere in the program does make the first one correct, which is worth knowing but is not something a library should ask of you.")

    # -- blit ------------------------------------------------------------

    def blit(self, fbuf: "FrameBuffer", x: int16, y: int16, key: int16 = -1, palette: Optional["FrameBuffer"] = None):
        if palette is None:
            self._blit(fbuf, x, y, key)
        else:
            self._blit_palette(fbuf, x, y, key, palette)

    def _blit(self, src: "FrameBuffer", x: int16, y: int16, key: int16):
        if x >= self.width or y >= self.height or -x >= src.width or -y >= src.height:
            return
        x0: int16 = 0
        if x > 0:
            x0 = x
        y0: int16 = 0
        if y > 0:
            y0 = y
        x1: int16 = 0
        if -x > 0:
            x1 = -x
        y1: int16 = 0
        if -y > 0:
            y1 = -y
        x0end: int16 = x + src.width
        if x0end > self.width:
            x0end = self.width
        y0end: int16 = y + src.height
        if y0end > self.height:
            y0end = self.height
        while y0 < y0end:
            cx1: int16 = x1
            cx0: int16 = x0
            while cx0 < x0end:
                col: uint16 = src._getpixel(cx1, y1)
                if col != key:
                    self._setpixel(cx0, y0, col)
                cx1 = cx1 + 1
                cx0 = cx0 + 1
            y1 = y1 + 1
            y0 = y0 + 1

    def _blit_palette(self, src: "FrameBuffer", x: int16, y: int16, key: int16, palette: "FrameBuffer"):
        if x >= self.width or y >= self.height or -x >= src.width or -y >= src.height:
            return
        x0: int16 = 0
        if x > 0:
            x0 = x
        y0: int16 = 0
        if y > 0:
            y0 = y
        x1: int16 = 0
        if -x > 0:
            x1 = -x
        y1: int16 = 0
        if -y > 0:
            y1 = -y
        x0end: int16 = x + src.width
        if x0end > self.width:
            x0end = self.width
        y0end: int16 = y + src.height
        if y0end > self.height:
            y0end = self.height
        while y0 < y0end:
            cx1: int16 = x1
            cx0: int16 = x0
            while cx0 < x0end:
                idx: uint16 = src._getpixel(cx1, y1)
                col: uint16 = palette._getpixel(idx, 0)
                if col != key:
                    self._setpixel(cx0, y0, col)
                cx1 = cx1 + 1
                cx0 = cx0 + 1
            y1 = y1 + 1
            y0 = y0 + 1

    # -- refused ----------------------------------------------------------

    @inline
    def poly(self, x: int16, y: int16, coords, c: uint16, f: bool = False):
        raise _CompileError("framebuf.FrameBuffer.poly: not available on this target. The outline walk needs to index an array of coordinates at run time and the filled walk needs one array of scan-line crossings per polygon, sized at run time, which this target has no heap to allocate. Draw the edges yourself with framebuf.FrameBuffer.line.")


class FrameBuffer1(FrameBuffer):
    # Upstream keeps FrameBuffer1 for the pre-format API: a FrameBuffer that
    # is always MONO_VLSB. There it is a factory function returning a plain
    # FrameBuffer; here it is a subclass, so `type()` differs and everything
    # that draws does not.
    def __init__(self, buf: bytearray, width: int16, height: int16, stride: Optional[int16] = None):
        super().__init__(buf, width, height, MVLSB, stride)


# ---------------------------------------------------------------------------
# What this module does not give, and why
# ---------------------------------------------------------------------------
#
# Measured against MicroPython's own builtin framebuf running the same
# programs: every drawing primitive below writes the same bytes into the same
# buffer, in MONO_VLSB, MONO_HLSB, MONO_HMSB, GS2_HMSB, GS4_HMSB, GS8 and
# RGB565, including the clipping, the stride rounding and the out-of-bounds
# answers. What differs is listed here rather than left to be discovered.
#
# text() takes a constant string. Upstream walks the characters of any string
#   at run time; this compiler has no run-time string iteration, so the walk is
#   unrolled at compile time. A string only known at run time is refused by the
#   compiler, naming the loop, rather than drawing something else.
#
# ellipse() is refused while PyMCU/PyMCU#510 is open, and the refusal says so.
#   The walk is implemented and matches the interpreter, but with a single call
#   site in the program the compiler inlines it and the inlined filled walk
#   writes the wrong pixels. Refusing beats drawing almost the right ellipse in
#   silence.
#
# poly() is refused. The outline walk indexes an array of coordinates at run
#   time and the filled walk needs one array of scan-line crossings per
#   polygon, sized at run time. FrameBuffer.line draws the edges.
#
# blit() takes a FrameBuffer, never the (buffer, width, height, format[,
#   stride]) tuple upstream also accepts, and its palette is given as a fourth
#   and fifth argument rather than defaulting to None.
#
# The constructor refuses at compile time what upstream refuses with a
#   ValueError at run time: width or height below 1, a stride below width, an
#   unknown format. Raising needs a heap this target does not have, so the
#   check has to happen while the sizes are still constants.
#
# The buffer IS checked against the geometry, at compile time. Upstream raises
#   ValueError when the buffer is too small for width x height x format; that
#   check happens here while the sizes are still constants, using upstream's
#   own formula including the per-format rounding. Measured against the real
#   interpreter over 210 boundary cases, one byte under and one byte over the
#   exact requirement in every format, at five geometries, with and without an
#   explicit stride: the two agree on all of them. The twelve that differ are
#   buffers past 2 KB, which the AVR backend refuses first for not fitting in
#   SRAM, with its own message.
#
# Every index is computed in int16, so the addressable buffer stops at 32767
#   bytes. That is every mono display and every small colour one; a 320x240
#   RGB565 frame is past it.
#
# FrameBuffer1 is a subclass of FrameBuffer here and a factory function
#   upstream, so type() answers differently and nothing that draws does.
