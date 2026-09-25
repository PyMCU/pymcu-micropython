import framebuf

buf = bytearray(128)
fb = framebuf.FrameBuffer(buf, 20, 16, framebuf.MONO_VLSB, 32)
fb.fill(0)
fb.text("Wide", 0, 0, 1)
fb.rect(1, 9, 16, 6, 1)
fb.line(0, 0, 19, 15, 1)
i = 0
while i < 128:
    print(buf[i])
    i = i + 1
print("END")
