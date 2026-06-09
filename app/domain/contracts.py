from typing import Dict, Mapping, Protocol, Sequence, Tuple

from app.domain.entities import CodeModuleMetrics, VulnerabilityPrediction

DatasetRecord = Mapping[str, object]
Dataset = Sequence[DatasetRecord]


class DatasetRepository(Protocol):
    def load(self) -> Dataset:
        ...

    def save(self, dataset: Dataset) -> None:
        ...


class ModelTrainer(Protocol):
    def train(self, dataset: Dataset) -> Dict[str, object]:
        ...


class ModelPredictor(Protocol):
    def predict(self, metrics: CodeModuleMetrics) -> Tuple[bool, float]:
        ...


class PredictionUseCase(Protocol):
    def execute(self, metrics: CodeModuleMetrics) -> VulnerabilityPrediction:
        ...
