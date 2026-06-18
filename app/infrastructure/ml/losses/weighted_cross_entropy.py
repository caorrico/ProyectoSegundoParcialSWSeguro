import torch
import torch.nn.functional as F

from .base import LossFunction


class BinaryWCELoss(LossFunction):
    """Weighted binary cross-entropy for imbalanced classes."""

    name = "wce"

    def __init__(self, weight_vuln: float = 10.0, weight_safe: float = 1.0, reduction: str = "mean"):
        super().__init__()
        self.weight_vuln = weight_vuln
        self.weight_safe = weight_safe
        self.reduction = reduction
        self.pos_weight = weight_vuln / weight_safe

    def forward(self, logits: torch.Tensor, targets: torch.Tensor) -> torch.Tensor:
        logits = logits.squeeze(-1)
        targets = targets.to(torch.float32)
        pos_weight = torch.tensor(self.pos_weight, device=logits.device, dtype=logits.dtype)
        return F.binary_cross_entropy_with_logits(
            logits,
            targets,
            pos_weight=pos_weight,
            reduction=self.reduction,
        )

    @property
    def config(self) -> dict:
        return {
            "weight_vuln": self.weight_vuln,
            "weight_safe": self.weight_safe,
            "pos_weight": self.pos_weight,
            "reduction": self.reduction,
        }
