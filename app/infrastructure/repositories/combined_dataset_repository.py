"""
Combined Dataset Repository: merges MegaVul (C/C++, Java), CodeXGLUE, and D2A
into a single training corpus for maximum diversity.
"""
from pathlib import Path
from app.domain.contracts import Dataset, DatasetRepository
from app.infrastructure.repositories.megavul_dataset_repository import MegaVulDatasetRepository
from app.infrastructure.repositories.codexglue_dataset_repository import CodeXGLUEDatasetRepository
from app.infrastructure.repositories.d2a_dataset_repository import D2ADatasetRepository
from app.infrastructure.repositories.reveal_dataset_repository import ReVealDatasetRepository
from app.infrastructure.repositories.vulberta_dataset_repository import VulBERTaDatasetRepository
from app.infrastructure.repositories.cvefixes_dataset_repository import CVEFixesDatasetRepository


class CombinedDatasetRepository(DatasetRepository):
    """Loads and merges multiple vulnerability datasets."""

    def __init__(self, limit_per_source: int | None = None):
        """
        Initialize the combined dataset repository.
        
        Args:
            limit_per_source: Maximum number of samples per source (None = use all data)
        """
        self._limit_per_source = limit_per_source

    def load(self) -> Dataset:
        combined: Dataset = []

        # 1. MegaVul C/C++
        megavul_cpp_path = Path("megavul/c_cpp/megavul_simple.json")
        if megavul_cpp_path.exists():
            try:
                repo = MegaVulDatasetRepository(megavul_cpp_path, limit=self._limit_per_source)
                data = repo.load()
                print(f"  [COMBINED] MegaVul C/C++: {len(data)} samples loaded")
                combined.extend(data)
            except Exception as e:
                print(f"  [WARN] MegaVul C/C++ failed: {e}")

        # 2. MegaVul Java
        megavul_java_path = Path("megavul/java/megavul_simple.json")
        if megavul_java_path.exists():
            try:
                repo = MegaVulDatasetRepository(megavul_java_path, limit=self._limit_per_source)
                data = repo.load()
                print(f"  [COMBINED] MegaVul Java: {len(data)} samples loaded")
                combined.extend(data)
            except Exception as e:
                print(f"  [WARN] MegaVul Java failed: {e}")

        # 3. CodeXGLUE
        codexglue_path = Path("data/codexglue/train.jsonl")
        if codexglue_path.exists():
            try:
                repo = CodeXGLUEDatasetRepository(codexglue_path, limit=self._limit_per_source)
                data = repo.load()
                print(f"  [COMBINED] CodeXGLUE: {len(data)} samples loaded")
                combined.extend(data)
            except Exception as e:
                print(f"  [WARN] CodeXGLUE failed: {e}")

        # 4. D2A (IBM)
        d2a_path = Path("data/d2a/train.jsonl")
        if d2a_path.exists():
            try:
                repo = D2ADatasetRepository(d2a_path, limit=self._limit_per_source)
                data = repo.load()
                print(f"  [COMBINED] D2A (IBM): {len(data)} samples loaded")
                combined.extend(data)
            except Exception as e:
                print(f"  [WARN] D2A failed: {e}")

        # 5. ReVeal (Chromium/Debian)
        reveal_path = Path("data/reveal/train.jsonl")
        if reveal_path.exists():
            try:
                repo = ReVealDatasetRepository(reveal_path, limit=self._limit_per_source)
                data = repo.load()
                print(f"  [COMBINED] ReVeal: {len(data)} samples loaded")
                combined.extend(data)
            except Exception as e:
                print(f"  [WARN] ReVeal failed: {e}")

        # 6. VulBERTa (Imperial College London)
        vulberta_path = Path("data/vulberta/train.jsonl")
        if vulberta_path.exists():
            try:
                repo = VulBERTaDatasetRepository(vulberta_path, limit=self._limit_per_source)
                data = repo.load()
                print(f"  [COMBINED] VulBERTa: {len(data)} samples loaded")
                combined.extend(data)
            except Exception as e:
                print(f"  [WARN] VulBERTa failed: {e}")
                
        # 7. CVEFixes
        cvefixes_path = Path("data/CVEFixes.csv/CVEFixes.csv")
        if cvefixes_path.exists():
            try:
                repo = CVEFixesDatasetRepository(cvefixes_path)
                data = repo.load()
                # Optionally limit CVEFixes too (since it's large)
                if self._limit_per_source and len(data) > self._limit_per_source:
                    import random
                    random.shuffle(data)
                    data = data[:self._limit_per_source]
                print(f"  [COMBINED] CVEFixes: {len(data)} samples loaded")
                combined.extend(data)
            except Exception as e:
                print(f"  [WARN] CVEFixes failed: {e}")

        if not combined:
            raise RuntimeError("No datasets found. Please download at least one dataset first.")

        print(f"  [COMBINED] Total: {len(combined)} samples from all sources")
        return combined

    def save(self, dataset: Dataset) -> None:
        raise NotImplementedError("CombinedDatasetRepository is read-only")

