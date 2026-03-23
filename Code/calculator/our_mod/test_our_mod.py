import pytest
from our_mod.our_mod import our_mod


def test_trivial_mod():
    assert our_mod(17) == 17, "Should be 17"


def test_for_negatives():
    assert our_mod(-3) == 3, "Should be 3"


@pytest.mark.parametrize("a,result", [(-3, 3)])
def test_multiples(a, result):
    assert result == our_mod(a)
