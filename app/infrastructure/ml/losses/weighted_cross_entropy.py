import torch
import torch.nn as nn
import torch.nn.functional as F

from .base import LossFunction


class BinaryWCELoss(LossFunction):
    \"\"\"
    Weighted Cross-Entropy (teoria.md líneas 9-15).
    L_WCE = -1/N * sum[w1*y*log(y) + w0*(1-y)*log(1-y)]
    Implementado via BCEWithLogitsLoss con pos_weight = weight_vuln / weight_safe
    \"\"\"
    name = 'wce'

    def __init__(self, weight_vuln: float = 10.0, weight_safe: float = 1.0, reduction: str = 'mean'):
        super().__init__()
        self.weight_vuln = weight_vuln
        self.weight_safe = weight_safe
        self.reduction = reduction
        self.pos_weight = weight_vuln / weight_safe

    def forward(self, logits: torch.Tensor, targets: torch.Tensor) -> torch.Tensor:
        logits = logits.squeeze(-1)
        targets = targets.to(torch.float32)

        loss = F.binary_cross_entropy_with_logits(
            logits, targets, pos_weight=torch.tensor(self.pos_weight), reduction=self.reduction
        )
        return loss

    @property
    def config(self) -> dict:
        return {
            'weight_vuln': self.weight_vuln,
            'weight_safe': self.weight_safe,
            'pos_weight': self.pos_weight,
            'reduction': self.reduction
        }
