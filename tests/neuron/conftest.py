import os

import pytest


def pytest_collection_modifyitems(config, items):
    """Tests under tests/neuron need a NeuronCore. The demo runs them on a stub device."""
    if os.environ.get("SGLANG_NEURON_DEVICE"):
        return
    skip = pytest.mark.skip(reason="needs a NeuronCore (set SGLANG_NEURON_DEVICE)")
    for item in items:
        if "neuron" in item.keywords:
            item.add_marker(skip)
