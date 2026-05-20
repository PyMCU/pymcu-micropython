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
    assert t == 0  # stub always returns 0


def test_ticks_diff_simple():
    assert ticks_diff(10, 3) == 7


def test_ticks_diff_zero():
    assert ticks_diff(0, 0) == 0


def test_ticks_diff_same():
    assert ticks_diff(5, 5) == 0
