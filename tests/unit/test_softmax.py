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


def test_temperature_flattens():
    sharp = softmax([0.0, 1.0])
    flat = softmax([0.0, 1.0], temperature=10.0)
    assert flat[1] - flat[0] < sharp[1] - sharp[0]


def test_temperature_must_be_positive():
    with pytest.raises(ValueError):
        softmax([1.0], temperature=0.0)
