from unittest.mock import patch
from pymcu_micropython.utime import sleep_ms, sleep_us, sleep, ticks_ms, ticks_diff


def test_sleep_ms_callable():
    sleep_ms(500)


def test_sleep_us_callable():
    sleep_us(100)


def test_sleep_callable():
    sleep(1)


def test_ticks_ms_returns_int():
    t = ticks_ms()
    assert isinstance(t, int)


def test_ticks_ms_delegates_to_millis():
    # ticks_ms() must delegate to hal.timer.millis(), not return a stub zero.
    import pymcu.hal.timer as _timer_hal
    with patch.object(_timer_hal, "millis", return_value=42):
        assert ticks_ms() == 42


def test_ticks_diff_simple():
    assert ticks_diff(10, 3) == 7


def test_ticks_diff_zero():
    assert ticks_diff(0, 0) == 0


def test_ticks_diff_same():
    assert ticks_diff(5, 5) == 0


def test_ticks_diff_large_values():
    assert ticks_diff(1000, 750) == 250
