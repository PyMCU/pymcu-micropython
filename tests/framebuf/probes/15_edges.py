import framebuf

buf = bytearray(64)
fb = framebuf.FrameBuffer(buf, 32, 16, framebuf.MONO_VLSB)
fb.fill(0)
print(fb.pixel(-1, 0))
print(fb.pixel(0, -1))
print(fb.pixel(32, 0))
print(fb.pixel(0, 16))
print(fb.pixel(0, 0))
fb.text("D", 4, 4)
fb.rect(0, 0, 1, 1, 1)
fb.rect(0, 0, 1, 1, 1, True)
fb.hline(0, 0, 0, 1)
fb.vline(0, 0, 0, 1)
fb.line(0, 0, 0, 0, 1)
i = 0
while i < 64:
    print(buf[i])
    i = i + 1
print("END")
