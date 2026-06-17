\"\"\"
Loss Functions Module para detección de vulnerabilidades.

Implementa Strategy Pattern + Factory Pattern para funciones de pérdida
robustas ante desequilibrio de clases (teoria.md).

Available losses:
- focal: BinaryFocalLoss (Focal Loss, Lin et al.)
- wce: BinaryWCELoss (Weighted Cross-Entropy)
- cb: ClassBalancedLoss (Class-Balanced Loss, Cui et al.)
\"\"\"

from .base import LossFunction
from .focal_loss import BinaryFocalLoss
from .weighted_cross_entropy import BinaryWCELoss
from .class_balanced_loss import ClassBalancedLoss
from .factory import LossFactory

__all__ = [
    'LossFunction',
    'BinaryFocalLoss',
    'BinaryWCELoss',
    'ClassBalancedLoss',
    'LossFactory',
]
