"""On-device smoke tests. In this demo the device is a CPU stub."""

import math
import random

import pytest

from sglang_neuron.kernels import rmsnorm

pytestmark = pytest.mark.neuron


def test_rmsnorm_matches_reference():
    rng = random.Random(0)
    x = [rng.uniform(-4, 4) for _ in range(256)]
    w = [rng.uniform(0.5, 1.5) for _ in range(256)]
    ref_scale = 1.0 / math.sqrt(math.fsum(v * v for v in x) / len(x) + 1e-6)
    ref = [v * ref_scale * g for v, g in zip(x, w)]
    assert rmsnorm(x, w) == pytest.approx(ref, rel=1e-6)
