import pytest

from sglang_neuron.config import NeuronConfig


def test_defaults():
    assert NeuronConfig().tp_size == 1


@pytest.mark.parametrize("tp", [0, 3, 6])
def test_tp_size_must_be_power_of_two(tp):
    with pytest.raises(ValueError):
        NeuronConfig(tp_size=tp)
