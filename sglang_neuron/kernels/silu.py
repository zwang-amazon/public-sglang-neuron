"""SiLU (swish) activation."""

import math
from collections.abc import Sequence


def _silu(v: float) -> float:
    # Both branches avoid exp() of a large positive number.
    if v >= 0:
        return v / (1.0 + math.exp(-v))
    e = math.exp(v)
    return v * e / (1.0 + e)


def silu(x: Sequence[float]) -> list[float]:
    """Return x * sigmoid(x), elementwise."""
    return [_silu(v) for v in x]
