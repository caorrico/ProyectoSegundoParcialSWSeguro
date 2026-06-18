from sklearn.ensemble import RandomForestClassifier
from app.infrastructure.ml.base_trainer import BaseTrainer


class RandomForestTrainer(BaseTrainer):
    def _create_base_model(self):
        return RandomForestClassifier(
            n_estimators=600,
            max_depth=None,
            min_samples_split=2,
            min_samples_leaf=1,
            class_weight={0: 1, 1: 2.5},
            max_features="sqrt",
            bootstrap=True,
            n_jobs=-1,
            random_state=self._random_state,
        )

    def _get_param_grid(self):
        return {
            'n_estimators': [400, 600, 800],
            'max_depth': [None, 30, 50],
            'min_samples_split': [2],
            'min_samples_leaf': [1],
            'class_weight': ["balanced", {0: 1, 1: 2.0}, {0: 1, 1: 3.0}],
            'max_features': ["sqrt", "log2"]
        }
