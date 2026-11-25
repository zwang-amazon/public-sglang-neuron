"""Numerically stable softmax on a single row."""

import math
from collections.abc import Sequence


def softmax(x: Sequence[float]) -> list[float]:
    """Return exp(x - max(x)) / sum(exp(x - max(x)))."""
    if not x:
        raise ValueError("x must not be empty")
    m = max(x)
    exps = [math.exp(v - m) for v in x]
    total = math.fsum(exps)
    return [e / total for e in exps]
