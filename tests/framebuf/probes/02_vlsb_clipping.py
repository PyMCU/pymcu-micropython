import framebuf

buf = bytearray(64)
fb = framebuf.FrameBuffer(buf, 32, 16, framebuf.MONO_VLSB)
fb.fill(0)
fb.fill_rect(-5, -5, 10, 10, 1)
fb.fill_rect(28, 12, 10, 10, 1)
fb.rect(-3, 4, 12, 6, 1)
fb.hline(-4, 1, 40, 1)
fb.vline(30, -4, 40, 1)
fb.line(-10, -10, 40, 30, 1)
fb.fill_rect(0, 0, 0, 5, 1)
fb.fill_rect(0, 0, 5, 0, 1)
fb.fill_rect(-20, 0, 5, 5, 1)
fb.fill_rect(40, 0, 5, 5, 1)
fb.pixel(-1, 0, 1)
fb.pixel(0, -1, 1)
fb.pixel(32, 0, 1)
fb.pixel(0, 16, 1)
i = 0
while i < 64:
    print(buf[i])
    i = i + 1
print("END")
