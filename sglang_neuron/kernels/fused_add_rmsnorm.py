"""Residual add followed by RMS normalization, in one pass."""

from collections.abc import Sequence

from sglang_neuron.kernels.rmsnorm import rmsnorm


def fused_add_rmsnorm(
    x: Sequence[float], residual: Sequence[float], weight: Sequence[float], eps: float = 1e-6
) -> tuple[list[float], list[float]]:
    """Return (rmsnorm(x + residual), x + residual)."""
    if len(x) != len(residual):
        raise ValueError("x and residual must have the same length")
    summed = [a + b for a, b in zip(x, residual)]
    return rmsnorm(summed, weight, eps), summed
