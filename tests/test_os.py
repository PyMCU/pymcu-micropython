import inspect

import pymcu_micropython.os as os_mod
import pymcu_micropython.uos as uos_mod
from pymcu.exceptions import CompileError


def test_uname_signature():
    # Upstream signature: uname() -> uname_result, no parameters.
    assert list(inspect.signature(os_mod.uname).parameters) == []


def test_uname_result_shape():
    # The five upstream fields, in upstream order.
    assert os_mod._Uname._fields == ("sysname", "nodename", "release", "version", "machine")


def test_uname_bare_call_refuses():
    # A bare uname() would need a runtime tuple object; the compiler answers
    # field reads and membership instead. Under CPython the same refusal is
    # the visible behaviour -- not a tuple of empty placeholder strings.
    try:
        os_mod.uname()
    except CompileError as e:
        assert "uname()" in str(e)
    else:
        raise AssertionError("uname() should refuse, not return placeholders")


def test_uos_is_os():
    # Upstream uos is the same module under the u-spelling.
    assert uos_mod.uname is os_mod.uname


def test_public_surface():
    # Only uname() -- no filesystem names, no import leaks beyond the
    # pymcu.types `inline` decorator (the layer-wide import-leak class the
    # underscore-alias pass removes; @inline must spell that literal name).
    machinery = {"inline"}
    assert set(n for n in dir(os_mod) if not n.startswith("_")) - machinery == {"uname"}
    assert set(n for n in dir(uos_mod) if not n.startswith("_")) - machinery == {"uname"}
