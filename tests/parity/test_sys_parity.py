from tests.parity._api import assert_case, pytest_generate_for_module


MODULE_NAME = "sys"

# The stdlib/sys stub is the shared typeshed file: a union of CPython's sys
# and MicroPython's, where most of the CPython-only names (sys.getsizeof,
# sys.setrecursionlimit, sys.audit, ...) exist on no real MicroPython port.
# Requiring them would be testing the layer against names a board does not
# have. The real MicroPython sys surface -- the members the firmware oracle
# on the Pico enumerates -- is exactly this set, and that is what the layer
# is compared against.
REAL_SYS = {
    "argv", "byteorder", "exit", "implementation", "maxsize", "modules",
    "path", "platform", "print_exception", "ps1", "ps2", "stderr", "stdin",
    "stdout", "version", "version_info",
}


def pytest_generate_tests(metafunc):
    pytest_generate_for_module(metafunc, MODULE_NAME, only=REAL_SYS)


def test_public_api_parity(case):
    assert_case(case)
