# Probes for surface this layer withholds

`13_ellipse.py` and the MicroPython output beside it are kept, not deleted:
they are what `FrameBuffer.ellipse` has to reproduce the day the refusal is
lifted. `ellipse` is implemented and correct under CPython and on the Uno
whenever the program calls it from more than one place; with a single call site
the compiler inlines the method and the inlined filled walk writes the wrong
pixels, so the layer refuses it rather than drawing almost the right ellipse in
silence. PyMCU/PyMCU#510 carries the reproduction and the controls. See `docs/limitations.md`.

Move the pair back into `probes/` and `expected/` when the refusal goes.
