from typing import Dict, Type

from .base import LossFunction
from .focal_loss import BinaryFocalLoss
from .weighted_cross_entropy import BinaryWCELoss
from .class_balanced_loss import ClassBalancedLoss


class LossFactory:
    \"\"\"Factory para crear instancias de funciones de pérdida (Factory Pattern).\"\"\"

    _registry: Dict[str, Type[LossFunction]] = {
        'focal': BinaryFocalLoss,
        'wce': BinaryWCELoss,
        'cb': ClassBalancedLoss,
    }

    @classmethod
    def create(cls, loss_type: str, **kwargs) -> LossFunction:
        \"\"\"Crea una instancia de la función de pérdida especificada.\"\"\"
        if loss_type not in cls._registry:
            available = ', '.join(cls._registry.keys())
            raise ValueError(f'Unknown loss type: {loss_type}. Available: {available}')
        return cls._registry[loss_type](**kwargs)

    @classmethod
    def register(cls, name: str, loss_class: Type[LossFunction]) -> None:
        \"\"\"Registra una nueva función de pérdida (Open/Closed Principle).\"\"\"
        cls._registry[name] = loss_class

    @classmethod
    def available_losses(cls) -> list[str]:
        \"\"\"Retorna lista de tipos de pérdida disponibles.\"\"\"
        return list(cls._registry.keys())
