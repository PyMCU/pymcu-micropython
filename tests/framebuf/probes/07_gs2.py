import framebuf

buf = bytearray(128)
fb = framebuf.FrameBuffer(buf, 32, 16, framebuf.GS2_HMSB)
fb.fill(0)
fb.fill(2)
fb.fill_rect(2, 2, 6, 6, 1)
fb.rect(12, 2, 8, 6, 3)
fb.line(0, 15, 31, 10, 1)
fb.pixel(5, 5, 3)
print(fb.pixel(5, 5))
print(fb.pixel(6, 5))
fb.text("Z", 20, 8, 3)
i = 0
while i < 128:
    print(buf[i])
    i = i + 1
print("END")
