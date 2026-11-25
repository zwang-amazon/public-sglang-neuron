"""RMS normalization on a single row."""

import math
from collections.abc import Sequence


def rmsnorm(x: Sequence[float], weight: Sequence[float], eps: float = 1e-6) -> list[float]:
    """Return x / sqrt(mean(x**2) + eps) * weight."""
    if len(x) != len(weight):
        raise ValueError("x and weight must have the same length")
    scale = 1.0 / math.sqrt(sum(v * v for v in x) / len(x) + eps)
    return [v * scale * w for v, w in zip(x, weight)]
