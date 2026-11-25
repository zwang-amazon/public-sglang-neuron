"""GELU activation, tanh approximation."""

import math
from collections.abc import Sequence

_C = math.sqrt(2.0 / math.pi)


def gelu(x: Sequence[float]) -> list[float]:
    """Return 0.5 * x * (1 + tanh(sqrt(2/pi) * (x + 0.044715 * x**3)))."""
    return [0.5 * v * (1.0 + math.tanh(_C * (v + 0.044715 * v**3))) for v in x]
