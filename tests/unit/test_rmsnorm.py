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


def test_length_mismatch():
    with pytest.raises(ValueError):
        rmsnorm([1.0], [1.0, 2.0])
