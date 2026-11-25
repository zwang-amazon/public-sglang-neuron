"""Numerically stable softmax on a single row."""

import math
from collections.abc import Sequence


def softmax(x: Sequence[float], temperature: float = 1.0) -> list[float]:
    """Return softmax(x / temperature), computed as exp(y - max(y)) / sum(exp(y - max(y)))."""
    if not x:
        raise ValueError("x must not be empty")
    if temperature <= 0:
        raise ValueError(f"temperature must be positive, got {temperature}")
    y = [v / temperature for v in x]
    m = max(y)
    exps = [math.exp(v - m) for v in y]
    total = math.fsum(exps)
    return [e / total for e in exps]
