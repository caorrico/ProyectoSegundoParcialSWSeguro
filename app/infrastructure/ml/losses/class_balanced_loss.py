import torch
import torch.nn as nn
import torch.nn.functional as F

from .base import LossFunction
from .focal_loss import BinaryFocalLoss


class ClassBalancedLoss(LossFunction):
    \"\"\"
    Class-Balanced Loss (teoria.md líneas 25-31).
    L_CB = (1-ß)/(1-ß^n) * L(p_t)
    ß = (N-1)/N, n = muestras en clase objetivo
    effective_num = (1 - ß^n) / (1 - ß)
    weight = 1 / effective_num
    \"\"\"
    name = 'cb'

    def __init__(
        self,
        beta: float = 0.9999,
        loss_type: str = 'focal',
        focal_gamma: float = 2.0,
        focal_alpha: float = 0.25,
        reduction: str = 'mean'
    ):
        super().__init__()
        self.beta = beta
        self.loss_type = loss_type
        self.focal_gamma = focal_gamma
        self.focal_alpha = focal_alpha
        self.reduction = reduction
        self._class_weights = None
        self._focal_loss = None

    def _compute_class_weights(self, targets: torch.Tensor) -> torch.Tensor:
        \"\"\"Calcula pesos CB basados en frecuencia de clases en el batch.\"\"\"
        n_vuln = targets.sum().item()
        n_safe = (1 - targets).sum().item()

        effective_num_vuln = (1 - self.beta ** n_vuln) / (1 - self.beta) if n_vuln > 0 else 1.0
        effective_num_safe = (1 - self.beta ** n_safe) / (1 - self.beta) if n_safe > 0 else 1.0

        weight_vuln = 1.0 / effective_num_vuln
        weight_safe = 1.0 / effective_num_safe

        # Normalizar para que el peso promedio sea 1
        total_weight = weight_vuln + weight_safe
        weight_vuln = weight_vuln * 2 / total_weight
        weight_safe = weight_safe * 2 / total_weight

        self._class_weights = torch.tensor([weight_safe, weight_vuln], device=targets.device, dtype=torch.float32)
        return self._class_weights

    def _get_focal_loss(self):
        if self._focal_loss is None:
            self._focal_loss = BinaryFocalLoss(
                alpha=self.focal_alpha,
                gamma=self.focal_gamma,
                reduction='none'
            )
        return self._focal_loss

    def forward(self, logits: torch.Tensor, targets: torch.Tensor) -> torch.Tensor:
        logits = logits.squeeze(-1)
        targets = targets.to(torch.float32)

        if self._class_weights is None:
            self._compute_class_weights(targets)

        if self.loss_type == 'focal':
            bce_loss = F.binary_cross_entropy_with_logits(logits, targets, reduction='none')
            probs = torch.sigmoid(logits)
            pt = targets * probs + (1 - targets) * (1 - probs)
            focal_weight = ((1 - pt) ** self.focal_gamma)
            alpha_weight = targets * self.focal_alpha + (1 - targets) * (1 - self.focal_alpha)
            loss = alpha_weight * focal_weight * bce_loss
            # Aplicar pesos CB
            class_weights = self._class_weights[targets.long()]
            loss = loss * class_weights
        elif self.loss_type == 'bce':
            loss = F.binary_cross_entropy_with_logits(
                logits, targets, reduction='none'
            )
            class_weights = self._class_weights[targets.long()]
            loss = loss * class_weights
        else:
            raise ValueError(f'Unknown loss_type: {self.loss_type}')

        if self.reduction == 'mean':
            return loss.mean()
        elif self.reduction == 'sum':
            return loss.sum()
        return loss

    @property
    def config(self) -> dict:
        return {
            'beta': self.beta,
            'loss_type': self.loss_type,
            'focal_gamma': self.focal_gamma,
            'focal_alpha': self.focal_alpha,
            'reduction': self.reduction
        }
