import pytest
from our_mult.our_mult import our_mult


def test_trivial_add():
    assert our_mult(2, 3) == 6, "Should be 6"


def test_for_negatives():
    assert our_mult(-2, -3) == 6, "Should be 6"


def test_for_mixed():
    assert our_mult(-2, 3) == -6, "Should be -6"


@pytest.mark.parametrize("a, b, result", [(1, 2, 2), (2, 4, 8), (3, 7, 21), (4, 8, 32)])
def test_multiples(a, b, result):
    assert result == our_mult(a, b)
