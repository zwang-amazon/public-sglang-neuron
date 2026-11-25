import pytest

from sglang_neuron.kernels.silu import silu


def test_known_values():
    assert silu([0.0, 1.0, -1.0]) == pytest.approx([0.0, 0.731059, -0.268941], abs=1e-6)


def test_large_negative_input_does_not_overflow():
    assert silu([-1000.0]) == [-0.0]
