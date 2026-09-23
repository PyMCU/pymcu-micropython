from tests.parity._api import assert_case, pytest_generate_for_module


MODULE_NAME = "os"

# The stdlib/os stub in micropython-stdlib-stubs is the shared typeshed file:
# a union of CPython's os and MicroPython's, where most of the CPython-only
# names (os.execv, os.kill, os.walk, os.cpu_count, ...) exist on no real
# MicroPython port. Requiring them would be testing the layer against names a
# board does not have. The real MicroPython os surface -- the members the
# firmware oracle on the Pico enumerates -- is exactly this set, and that is
# what the layer is compared against. (VfsFat/VfsLfs2 are real upstream but
# not declared in the os stub, so they generate no case.)
REAL_OS = {
    "chdir", "dupterm", "getcwd", "ilistdir", "listdir", "mkdir", "mount",
    "remove", "rename", "rmdir", "stat", "statvfs", "sync", "umount",
    "uname", "unlink", "urandom", "VfsFat", "VfsLfs2",
}


def pytest_generate_tests(metafunc):
    pytest_generate_for_module(metafunc, MODULE_NAME, only=REAL_OS)


def test_public_api_parity(case):
    assert_case(case)
