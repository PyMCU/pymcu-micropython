import framebuf

buf = bytearray(64)
fb = framebuf.FrameBuffer(buf, 32, 16, framebuf.MONO_VLSB)
fb.fill(1)
fb.fill(0)
fb.hline(0, 0, 32, 1)
fb.vline(0, 0, 16, 1)
fb.rect(2, 2, 10, 6, 1)
fb.rect(14, 2, 10, 6, 1, True)
fb.fill_rect(26, 2, 4, 4, 1)
fb.line(0, 15, 31, 8, 1)
fb.line(31, 15, 0, 9, 1)
fb.line(5, 0, 5, 15, 1)
fb.line(0, 5, 31, 5, 1)
fb.line(7, 7, 7, 7, 1)
fb.pixel(20, 12, 1)
fb.pixel(21, 12, 0)
print(fb.pixel(20, 12))
print(fb.pixel(21, 12))
i = 0
while i < 64:
    print(buf[i])
    i = i + 1
print("END")
