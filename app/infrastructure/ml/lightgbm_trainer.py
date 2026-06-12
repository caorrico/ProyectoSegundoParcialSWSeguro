from lightgbm import LGBMClassifier
from app.infrastructure.ml.base_trainer import BaseTrainer


class LightGBMTrainer(BaseTrainer):
    def _create_base_model(self):
        return LGBMClassifier(
            n_estimators=180,
            max_depth=10,
            class_weight="balanced",
            random_state=self._random_state,
        )
