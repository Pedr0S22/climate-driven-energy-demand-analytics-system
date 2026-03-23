import pytest
from our_sub.our_sub import our_sub


def test_trivial_sub():
    assert our_sub(5, 3) == 2, "Should be 2"


def test_for_negatives():
    assert our_sub(-5, -3) == -2, "Should be -2"


def test_for_mixed():
    assert our_sub(-2, 3) == -5, "Should be -5"


@pytest.mark.parametrize("a, b, result", [(10, 5, 5), (2, 4, -2), (0, 7, -7), (-4, -8, 4)])
def test_multiples(a, b, result):
    assert result == our_sub(a, b)
