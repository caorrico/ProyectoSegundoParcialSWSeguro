from xgboost import XGBClassifier
from app.infrastructure.ml.base_trainer import BaseTrainer


class XGBoostTrainer(BaseTrainer):
    def _create_base_model(self):
        return XGBClassifier(
            n_estimators=180,
            max_depth=6,
            learning_rate=0.1,
            scale_pos_weight=1, # Equivalent to class_weight="balanced" if dataset is roughly equal
            random_state=self._random_state,
            eval_metric="logloss"
        )
