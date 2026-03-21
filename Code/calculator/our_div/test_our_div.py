import pytest
from our_div import our_div

def test_trivial_div():
    assert our_div(10, 2) == 5, "Should be 5"

def test_for_negatives():
    assert our_div(-10, 2) == -5, "Should be -5"
    assert our_div(10, -2) == -5, "Should be -5"
    assert our_div(-10, -2) == 5, "Should be 5"

def test_div_by_zero():
    with pytest.raises(ZeroDivisionError):
        our_div(10, 0)

@pytest.mark.parametrize("a, b, result", [
    (10, 2, 5),
    (20, 5, 4),
    (0, 10, 0),
    pytest.param(10, 0, ZeroDivisionError, id="div_by_zero")
])

def test_multiples(a, b, result):
    if result == ZeroDivisionError:
        with pytest.raises(ZeroDivisionError):
            our_div(a, b)
    else:
        assert our_div(a, b) == result