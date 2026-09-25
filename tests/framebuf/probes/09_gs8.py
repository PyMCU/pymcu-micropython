import framebuf

buf = bytearray(512)
fb = framebuf.FrameBuffer(buf, 32, 16, framebuf.GS8)
fb.fill(0)
fb.fill(200)
fb.fill_rect(2, 2, 6, 6, 17)
fb.rect(12, 2, 8, 6, 255)
fb.line(0, 15, 31, 10, 33)
fb.pixel(5, 5, 99)
print(fb.pixel(5, 5))
print(fb.pixel(6, 5))
fb.text("Z", 20, 8, 7)
i = 0
while i < 512:
    print(buf[i])
    i = i + 1
print("END")
