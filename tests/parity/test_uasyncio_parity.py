from tests.parity._api import assert_case, pytest_generate_for_module


MODULE_NAME = "uasyncio"

# The uasyncio stub is `from asyncio import *` over the shared CPython
# typeshed asyncio surface -- hundreds of names no MicroPython board has.
# The oracle is the measured MicroPython 1.21 firmware surface (the campaign
# probe's dir() over a real board), so only those names generate cases.
# Upstream's own module-internal imports (`sys`, `select`, `ticks`, `core`,
# `_attrs`) are real attributes on the board and are listed for completeness;
# the stub collector cannot produce them, so they generate no case either way.
_REAL_UASYNCIO_SURFACE = {
    "CancelledError",
    "Event", "Event.__init__", "Event.clear", "Event.is_set", "Event.set", "Event.wait",
    "IOQueue", "IOQueue.__init__", "IOQueue.queue_read", "IOQueue.queue_write",
    "IOQueue.remove", "IOQueue.wait_io_event",
    "Lock", "Lock.__init__", "Lock.acquire", "Lock.locked", "Lock.release",
    "Loop", "Loop.call_exception_handler", "Loop.close", "Loop.create_task",
    "Loop.default_exception_handler", "Loop.get_exception_handler",
    "Loop.run_forever", "Loop.run_until_complete", "Loop.set_exception_handler",
    "Loop.stop",
    "SingletonGenerator", "SingletonGenerator.__init__",
    "SingletonGenerator.__iter__", "SingletonGenerator.__next__",
    "StreamReader", "StreamReader.__init__", "StreamReader.aclose",
    "StreamReader.awrite", "StreamReader.awritestr", "StreamReader.close",
    "StreamReader.drain", "StreamReader.get_extra_info", "StreamReader.read",
    "StreamReader.readexactly", "StreamReader.readinto", "StreamReader.readline",
    "StreamReader.wait_closed", "StreamReader.write",
    "StreamWriter", "StreamWriter.__init__", "StreamWriter.aclose",
    "StreamWriter.awrite", "StreamWriter.awritestr", "StreamWriter.close",
    "StreamWriter.drain", "StreamWriter.get_extra_info", "StreamWriter.read",
    "StreamWriter.readexactly", "StreamWriter.readinto", "StreamWriter.readline",
    "StreamWriter.wait_closed", "StreamWriter.write",
    "Task",
    "TaskQueue", "TaskQueue.peek", "TaskQueue.pop", "TaskQueue.push", "TaskQueue.remove",
    "ThreadSafeFlag", "ThreadSafeFlag.__init__", "ThreadSafeFlag.clear",
    "ThreadSafeFlag.ioctl", "ThreadSafeFlag.set", "ThreadSafeFlag.wait",
    "TimeoutError",
    "__version__",
    "create_task", "current_task", "gather", "get_event_loop", "new_event_loop",
    "open_connection", "run", "run_until_complete", "sleep", "sleep_ms",
    "start_server", "wait_for", "wait_for_ms",
}


def pytest_generate_tests(metafunc):
    pytest_generate_for_module(metafunc, MODULE_NAME, only=_REAL_UASYNCIO_SURFACE)


def test_public_api_parity(case):
    assert_case(case)
