import framebuf

buf = bytearray(256)
fb = framebuf.FrameBuffer(buf, 64, 32, framebuf.MONO_VLSB)
fb.fill(0)
fb.text("Hello, World!", 0, 0, 1)
fb.text("0123456789", 0, 8, 1)
fb.text("~{}[]<>?/\\|", 0, 16, 1)
fb.text("clip", -6, 24, 1)
fb.text("edge", 60, 24, 1)
i = 0
while i < 256:
    print(buf[i])
    i = i + 1
fb.fill(1)
fb.text("inv", 8, 8, 0)
i = 0
while i < 256:
    print(buf[i])
    i = i + 1
print("END")
