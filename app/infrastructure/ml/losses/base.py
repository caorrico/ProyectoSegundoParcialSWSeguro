from abc import ABC, abstractmethod
import torch
import torch.nn as nn


class LossFunction(ABC, nn.Module):
    """Strategy interface for loss functions."""

    @abstractmethod
    def forward(self, logits: torch.Tensor, targets: torch.Tensor) -> torch.Tensor:
        pass

    @property
    @abstractmethod
    def name(self) -> str:
        """Unique identifier: 'focal' | 'wce' | 'cb'"""
        pass

    @property
    @abstractmethod
    def config(self) -> dict:
        """Parameters for logging/reproducibility."""
        pass
