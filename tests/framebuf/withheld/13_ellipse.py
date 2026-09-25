import framebuf

buf = bytearray(256)
fb = framebuf.FrameBuffer(buf, 64, 32, framebuf.MONO_VLSB)
fb.fill(0)
fb.ellipse(10, 10, 8, 6, 1)
fb.ellipse(40, 16, 10, 10, 1, True)
fb.ellipse(30, 4, 0, 0, 1)
fb.ellipse(55, 25, 6, 4, 1, False, 3)
fb.ellipse(5, 28, 9, 7, 1, True, 9)
i = 0
while i < 256:
    print(buf[i])
    i = i + 1
print("END")
