from typing import Dict, Mapping, Protocol, Sequence, Tuple, Union

from app.domain.entities import CodeModuleMetrics, RawCodeModule, VulnerabilityPrediction

DatasetRecord = Mapping[str, object]
Dataset = Sequence[DatasetRecord]


class DatasetRepository(Protocol):
    def load(self) -> Dataset:
        ...

    def save(self, dataset: Dataset) -> None:
        ...


class ModelTrainer(Protocol):
    def train(self, dataset: Dataset, tune: bool = False) -> Dict[str, object]:
        ...


class ModelPredictor(Protocol):
    def predict(self, metrics: Union[CodeModuleMetrics, RawCodeModule]) -> Tuple[bool, float]:
        ...

    def generate_explanation(self, metrics: Union[CodeModuleMetrics, RawCodeModule], report_path: "Path") -> None:
        ...

class PredictionUseCase(Protocol):
    def execute(self, metrics: Union[CodeModuleMetrics, RawCodeModule]) -> VulnerabilityPrediction:
        ...
