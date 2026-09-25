import framebuf

dst = bytearray(512)
src = bytearray(16)
pal = bytearray(4)
fd = framebuf.FrameBuffer(dst, 32, 16, framebuf.GS8)
fs = framebuf.FrameBuffer(src, 16, 8, framebuf.MONO_VLSB)
fp = framebuf.FrameBuffer(pal, 2, 1, framebuf.GS8)
fd.fill(0)
fs.fill(0)
fs.text("q", 0, 0, 1)
fp.pixel(0, 0, 4)
fp.pixel(1, 0, 200)
fd.blit(fs, 2, 3, -1, fp)
i = 0
while i < 512:
    print(dst[i])
    i = i + 1
print("END")
