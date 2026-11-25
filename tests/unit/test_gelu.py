import pytest

from sglang_neuron.kernels.gelu import gelu


def test_known_values():
    assert gelu([0.0, 1.0, -1.0]) == pytest.approx([0.0, 0.841192, -0.158808], abs=1e-6)
