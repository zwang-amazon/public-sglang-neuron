import pytest

from sglang_neuron.kernels import fused_add_rmsnorm, rmsnorm


def test_matches_add_then_rmsnorm():
    x, r, w = [1.0, 2.0, 3.0], [0.5, -1.0, 2.0], [1.0, 0.5, 2.0]
    out, summed = fused_add_rmsnorm(x, r, w)
    assert summed == [1.5, 1.0, 5.0]
    assert out == pytest.approx(rmsnorm(summed, w))


def test_length_mismatch():
    with pytest.raises(ValueError):
        fused_add_rmsnorm([1.0], [1.0, 2.0], [1.0])
