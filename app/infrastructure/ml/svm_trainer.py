from sklearn.svm import SVC
from app.infrastructure.ml.base_trainer import BaseTrainer


class SVMTrainer(BaseTrainer):
    def _create_base_model(self):
        return SVC(
            probability=True, 
            class_weight="balanced", 
            random_state=self._random_state,
        )
