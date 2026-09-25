import framebuf

buf = bytearray(256)
fb = framebuf.FrameBuffer(buf, 32, 16, framebuf.GS4_HMSB)
fb.fill(0)
fb.fill(9)
fb.fill_rect(2, 2, 6, 6, 1)
fb.rect(12, 2, 8, 6, 15)
fb.line(0, 15, 31, 10, 4)
fb.pixel(5, 5, 7)
print(fb.pixel(5, 5))
print(fb.pixel(6, 5))
fb.text("Z", 20, 8, 12)
i = 0
while i < 256:
    print(buf[i])
    i = i + 1
print("END")
