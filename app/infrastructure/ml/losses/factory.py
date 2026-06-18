from .base import LossFunction
from .class_balanced_loss import ClassBalancedLoss
from .focal_loss import BinaryFocalLoss
from .weighted_cross_entropy import BinaryWCELoss


class LossFactory:
    """Factory for creating configured loss functions."""

    _registry: dict[str, type[LossFunction]] = {
        "focal": BinaryFocalLoss,
        "wce": BinaryWCELoss,
        "cb": ClassBalancedLoss,
    }

    @classmethod
    def create(cls, loss_type: str, **kwargs) -> LossFunction:
        if loss_type not in cls._registry:
            available = ", ".join(cls._registry.keys())
            raise ValueError(f"Unknown loss type: {loss_type}. Available: {available}")
        return cls._registry[loss_type](**kwargs)

    @classmethod
    def register(cls, name: str, loss_class: type[LossFunction]) -> None:
        cls._registry[name] = loss_class

    @classmethod
    def available_losses(cls) -> list[str]:
        return list(cls._registry.keys())
