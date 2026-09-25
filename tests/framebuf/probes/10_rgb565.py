import framebuf

buf = bytearray(256)
fb = framebuf.FrameBuffer(buf, 16, 8, framebuf.RGB565)
fb.fill(0)
fb.fill(1234)
fb.fill_rect(1, 1, 4, 4, 65535)
fb.rect(7, 1, 6, 5, 31)
fb.line(0, 7, 15, 0, 2016)
fb.pixel(3, 3, 63488)
print(fb.pixel(3, 3))
print(fb.pixel(4, 3))
fb.text("Z", 6, 0, 1023)
i = 0
while i < 256:
    print(buf[i])
    i = i + 1
print("END")
