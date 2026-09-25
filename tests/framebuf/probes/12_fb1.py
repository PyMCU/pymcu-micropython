import framebuf

buf = bytearray(64)
fb = framebuf.FrameBuffer1(buf, 32, 16)
fb.fill(0)
fb.text("Fb1", 2, 3, 1)
fb.rect(0, 0, 32, 16, 1)
i = 0
while i < 64:
    print(buf[i])
    i = i + 1
print("END")
