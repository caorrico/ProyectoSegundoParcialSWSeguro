from sklearn.ensemble import RandomForestClassifier
from app.infrastructure.ml.base_trainer import BaseTrainer


class RandomForestTrainer(BaseTrainer):
    def _create_base_model(self):
        return RandomForestClassifier(
            n_estimators=180,
            max_depth=10,
            class_weight="balanced",
            random_state=self._random_state,
        )

    def _get_param_grid(self):
        return {
            'n_estimators': [100, 200, 300, 500],
            'max_depth': [None, 10, 20, 30],
            'min_samples_split': [2, 5, 10],
            'min_samples_leaf': [1, 2, 4]
        }
