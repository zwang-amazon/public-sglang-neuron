import math

import pytest

from sglang_neuron.kernels.softmax import softmax


def test_sums_to_one_for_large_inputs():
    out = softmax([1000.0, 1001.0, 1002.0])
    assert math.fsum(out) == pytest.approx(1.0)
    assert out[2] > out[1] > out[0]


def test_empty_row():
    with pytest.raises(ValueError):
        softmax([])
