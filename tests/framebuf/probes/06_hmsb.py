import framebuf

buf = bytearray(64)
fb = framebuf.FrameBuffer(buf, 32, 16, framebuf.MONO_HMSB)
fb.fill(0)
fb.text("Hi", 1, 1, 1)
fb.rect(3, 9, 12, 5, 1)
fb.fill_rect(20, 9, 6, 5, 1)
fb.line(0, 0, 31, 15, 1)
fb.pixel(2, 2, 1)
print(fb.pixel(2, 2))
print(fb.pixel(3, 2))
i = 0
while i < 64:
    print(buf[i])
    i = i + 1
fb.scroll(1, 1)
i = 0
while i < 64:
    print(buf[i])
    i = i + 1
print("END")
