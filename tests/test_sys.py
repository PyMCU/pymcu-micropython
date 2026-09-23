import pymcu_micropython.sys as sys_mod
import pymcu_micropython.usys as usys_mod


def test_implementation_name():
    # The layer IS the claim: a program built against pymcu-micropython is the
    # same program that runs under MicroPython, so the interpreter-identity
    # guard must answer "micropython" here too.
    assert sys_mod.implementation.name == "micropython"


def test_implementation_version_absent():
    # version has no runtime form: the compiler substitutes (1, 29, 0) -- the
    # MicroPython API surface the parity suite pins against -- at the
    # `sys.implementation.version[i]` fold. The OBJECT carries no tuple, so a
    # binding the fold cannot see (`impl = sys.implementation`) refuses the
    # attribute instead of answering a placeholder.
    assert not hasattr(sys_mod.implementation, "version")


def test_platform_placeholder():
    # Placeholder for CPython/IDEs; the compiler substitutes the per-board
    # string ("rp2" on the Pico, the chip name where no upstream port exists).
    assert sys_mod.platform == "rp2"


def test_usys_is_sys():
    # Upstream usys is the same module under the u-spelling.
    assert usys_mod.implementation is sys_mod.implementation
    assert usys_mod.platform is sys_mod.platform


def test_public_surface():
    # Only implementation and platform -- no runtime-dependent names
    # (argv, byteorder, exit, maxsize, modules, path, print_exception,
    # stdin/stdout/stderr, version, version_info) and no import leaks.
    assert sorted(n for n in dir(sys_mod) if not n.startswith("_")) == ["implementation", "platform"]
    assert sorted(n for n in dir(usys_mod) if not n.startswith("_")) == ["implementation", "platform"]
