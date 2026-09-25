import framebuf

dst = bytearray(64)
src = bytearray(16)
fd = framebuf.FrameBuffer(dst, 32, 16, framebuf.MONO_VLSB)
fs = framebuf.FrameBuffer(src, 16, 8, framebuf.MONO_VLSB)
fd.fill(0)
fs.fill(0)
fs.text("ab", 0, 0, 1)
fd.blit(fs, 3, 4)
fd.blit(fs, -4, 9)
fd.blit(fs, 26, 1)
fd.blit(fs, 40, 0)
fd.blit(fs, 0, 20)
i = 0
while i < 64:
    print(dst[i])
    i = i + 1
fd.fill(0)
fd.blit(fs, 2, 2, 0)
i = 0
while i < 64:
    print(dst[i])
    i = i + 1
print("END")
