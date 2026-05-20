from pymcu_micropython.micropython import const, native, viper


def test_const_is_identity():
    assert const(42) == 42
    assert const(9600) == 9600
    assert const(0) == 0


def test_const_with_expression():
    assert const(1 + 1) == 2


def test_native_is_identity_decorator():
    @native
    def f():
        return 1

    assert f() == 1


def test_viper_is_identity_decorator():
    @viper
    def g():
        return 2

    assert g() == 2


def test_decorators_preserve_callable():
    @native
    def add(a, b):
        return a + b

    assert add(3, 4) == 7
