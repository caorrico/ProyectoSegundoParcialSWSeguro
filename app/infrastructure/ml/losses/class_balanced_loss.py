import torch
import torch.nn.functional as F

from .base import LossFunction


class ClassBalancedLoss(LossFunction):
    """Class-balanced binary loss with optional focal weighting."""

    name = "cb"

    def __init__(
        self,
        beta: float = 0.9999,
        loss_type: str = "focal",
        focal_gamma: float = 2.0,
        focal_alpha: float = 0.25,
        reduction: str = "mean",
    ):
        super().__init__()
        self.beta = beta
        self.loss_type = loss_type
        self.focal_gamma = focal_gamma
        self.focal_alpha = focal_alpha
        self.reduction = reduction

    def _compute_class_weights(self, targets: torch.Tensor) -> torch.Tensor:
        n_vuln = targets.sum().item()
        n_safe = (1 - targets).sum().item()
        effective_num_vuln = (1 - self.beta**n_vuln) / (1 - self.beta) if n_vuln > 0 else 1.0
        effective_num_safe = (1 - self.beta**n_safe) / (1 - self.beta) if n_safe > 0 else 1.0
        weight_vuln = 1.0 / effective_num_vuln
        weight_safe = 1.0 / effective_num_safe
        total_weight = weight_vuln + weight_safe
        return torch.tensor(
            [weight_safe * 2 / total_weight, weight_vuln * 2 / total_weight],
            device=targets.device,
            dtype=torch.float32,
        )

    def forward(self, logits: torch.Tensor, targets: torch.Tensor) -> torch.Tensor:
        logits = logits.squeeze(-1)
        targets = targets.to(torch.float32)
        class_weights = self._compute_class_weights(targets)[targets.long()]
        loss = F.binary_cross_entropy_with_logits(logits, targets, reduction="none")
        if self.loss_type == "focal":
            probs = torch.sigmoid(logits)
            pt = targets * probs + (1 - targets) * (1 - probs)
            focal_weight = (1 - pt) ** self.focal_gamma
            alpha_weight = targets * self.focal_alpha + (1 - targets) * (1 - self.focal_alpha)
            loss = alpha_weight * focal_weight * loss
        elif self.loss_type != "bce":
            raise ValueError(f"Unknown loss_type: {self.loss_type}")
        loss = loss * class_weights
        if self.reduction == "mean":
            return loss.mean()
        if self.reduction == "sum":
            return loss.sum()
        return loss

    @property
    def config(self) -> dict:
        return {
            "beta": self.beta,
            "loss_type": self.loss_type,
            "focal_gamma": self.focal_gamma,
            "focal_alpha": self.focal_alpha,
            "reduction": self.reduction,
        }
