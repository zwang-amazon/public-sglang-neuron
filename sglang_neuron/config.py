"""Runtime configuration for the demo plugin."""

from dataclasses import dataclass


@dataclass(frozen=True)
class NeuronConfig:
    """Parallelism and batching settings."""

    tp_size: int = 1
    max_batch_size: int = 8

    def __post_init__(self) -> None:
        if self.tp_size < 1 or self.tp_size & (self.tp_size - 1):
            raise ValueError(f"tp_size must be a power of two, got {self.tp_size}")
        if self.max_batch_size < 1:
            raise ValueError(f"max_batch_size must be positive, got {self.max_batch_size}")
