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
    assert usys_mod.version is sys_mod.version


def test_version_string():
    # Language level + pinned API surface (the parity suite pins
    # micropython-rp2-stubs>=1.29.0). Upstream appends the firmware build
    # date; the layer states only the facts it can honestly claim.
    assert sys_mod.version == "3.4.0; MicroPython v1.29.0"


def test_version_info_absent():
    # version_info has no runtime form: a tuple attribute cannot materialize
    # honestly under pymcuc, so the compiler folds `sys.version_info[i]` to
    # (3, 4, 0)[i] -- the Python language version upstream reports -- and the
    # bare attribute refuses, the same contract implementation.version holds.
    assert not hasattr(sys_mod, "version_info")


def test_target_constants():
    # Pure target facts: every chip this layer compiles for is little-endian
    # and addresses a 32-bit int.
    assert sys_mod.byteorder == "little"
    assert sys_mod.maxsize == 2147483647


def test_public_surface():
    # implementation + platform + the honest constants -- no runtime-dependent
    # names (argv, exit, modules, path, print_exception, ps1/ps2,
    # stdin/stdout/stderr), no fold-only names (version_info), and no import
    # leaks.
    expected = ["byteorder", "implementation", "maxsize", "platform", "version"]
    assert sorted(n for n in dir(sys_mod) if not n.startswith("_")) == expected
    assert sorted(n for n in dir(usys_mod) if not n.startswith("_")) == expected
