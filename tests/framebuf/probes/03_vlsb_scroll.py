import framebuf

buf = bytearray(64)
fb = framebuf.FrameBuffer(buf, 32, 16, framebuf.MONO_VLSB)
fb.fill(0)
fb.text("Ab", 3, 4, 1)
fb.scroll(3, 0)
i = 0
while i < 64:
    print(buf[i])
    i = i + 1
fb.scroll(-2, 0)
i = 0
while i < 64:
    print(buf[i])
    i = i + 1
fb.scroll(0, 5)
i = 0
while i < 64:
    print(buf[i])
    i = i + 1
fb.scroll(0, -3)
i = 0
while i < 64:
    print(buf[i])
    i = i + 1
fb.scroll(2, -2)
i = 0
while i < 64:
    print(buf[i])
    i = i + 1
fb.scroll(40, 0)
fb.scroll(0, 40)
fb.scroll(-40, 0)
fb.scroll(0, -40)
i = 0
while i < 64:
    print(buf[i])
    i = i + 1
print("END")
