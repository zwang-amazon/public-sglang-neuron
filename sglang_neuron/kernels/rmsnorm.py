"""RMS normalization on a single row."""

import math
from collections.abc import Sequence


def rmsnorm(x: Sequence[float], weight: Sequence[float], eps: float = 1e-6) -> list[float]:
    """Return x / sqrt(mean(x**2) + eps) * weight, elementwise. eps must be finite, >= 0."""
    if not x:
        raise ValueError("x must not be empty")
    if not math.isfinite(eps) or eps < 0:
        raise ValueError(f"eps must be finite and non-negative, got {eps}")
    if len(x) != len(weight):
        raise ValueError("x and weight must have the same length")
    # fsum keeps the mean of squares exact for long rows with mixed magnitudes.
    scale = 1.0 / math.sqrt(math.fsum(v * v for v in x) / len(x) + eps)
    return [v * scale * w for v, w in zip(x, weight)]
