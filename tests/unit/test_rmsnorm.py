import math

import pytest

from sglang_neuron.kernels import rmsnorm


def test_unit_rms_row_is_unchanged():
    out = rmsnorm([1.0, -1.0, 1.0, -1.0], [1.0] * 4, eps=0.0)
    assert out == pytest.approx([1.0, -1.0, 1.0, -1.0])


def test_weight_scales_output():
    out = rmsnorm([3.0, 4.0], [2.0, 0.5], eps=0.0)
    rms = math.sqrt((9 + 16) / 2)
    assert out == pytest.approx([2 * 3 / rms, 0.5 * 4 / rms])


def test_empty_row():
    with pytest.raises(ValueError, match="empty"):
        rmsnorm([], [])


def test_length_mismatch():
    with pytest.raises(ValueError):
        rmsnorm([1.0], [1.0, 2.0])


def test_long_row_with_mixed_magnitudes():
    x = [1e8] + [1.0] * 10_000
    exact = 1.0 / math.sqrt(math.fsum(v * v for v in x) / len(x) + 1e-6)
    assert rmsnorm(x, [1.0] * len(x))[1] == exact


def test_eps_keeps_zero_row_finite():
    assert rmsnorm([0.0, 0.0], [1.0, 1.0]) == [0.0, 0.0]


def test_negative_eps():
    with pytest.raises(ValueError, match="eps"):
        rmsnorm([1.0], [1.0], eps=-1.0)
