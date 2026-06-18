"""
FastAPI endpoint para el modelo de minería de datos de vulnerabilidades.
Se despliega en Render/Railway para exponer las predicciones via HTTP.
"""
from typing import Optional

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

from app.domain.entities import RawCodeModule
from app.shared.settings import Settings
from app.infrastructure.ml.random_forest_predictor import RandomForestPredictor
from app.application.use_cases.predict_vulnerability import PredictVulnerabilityUseCase

settings = Settings()
app = FastAPI(
    title="SecureDataMining API",
    description="API de detección de vulnerabilidades en código fuente usando Minería de Datos (Random Forest + AST + TF-IDF). Prohibido uso de LLMs.",
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)


class PredictRequest(BaseModel):
    code: str
    filename: Optional[str] = "snippet.c"


class PredictResponse(BaseModel):
    is_vulnerable: bool
    risk_probability: float
    risk_level: str
    recommendation: str
    vulnerability_types: list[str]
    cwe_ids: list[str]
    filename: str


class ScanRequest(BaseModel):
    files: list[dict]  # [{"filename": "x.cpp", "code": "..."}, ...]


class HealthResponse(BaseModel):
    status: str
    model_loaded: bool
    model_path: str
    version: str


def _get_use_case() -> PredictVulnerabilityUseCase:
    model_path = settings.model_path
    if not model_path.exists():
        raise HTTPException(
            status_code=503,
            detail="Modelo no entrenado. Ejecutar: python -m app.interfaces.cli train --use-owasp"
        )
    predictor = RandomForestPredictor(model_path)
    return PredictVulnerabilityUseCase(predictor)


@app.get("/", include_in_schema=False)
def root():
    return {"message": "SecureDataMining API — /docs para ver la documentación"}


@app.get("/health", response_model=HealthResponse)
def health_check():
    """Endpoint de salud para Render/Railway health checks."""
    model_path = settings.model_path
    return HealthResponse(
        status="ok",
        model_loaded=model_path.exists(),
        model_path=str(model_path),
        version="1.0.0",
    )


@app.post("/predict", response_model=PredictResponse)
def predict_vulnerability(request: PredictRequest):
    """
    Clasifica un fragmento de código fuente como SEGURO o VULNERABLE.
    Usa Random Forest entrenado en dataset OWASP Top 10:2025.
    Prohibido LLMs — modelo de minería de datos tradicional.
    """
    if not request.code.strip():
        raise HTTPException(status_code=400, detail="El campo 'code' no puede estar vacío.")

    try:
        use_case = _get_use_case()
        metrics = RawCodeModule(raw_code=request.code)
        prediction = use_case.execute(metrics)
        return PredictResponse(
            is_vulnerable=prediction.is_vulnerable,
            risk_probability=round(prediction.risk_probability, 4),
            risk_level=prediction.risk_level.value,
            recommendation=prediction.recommendation,
            vulnerability_types=prediction.vulnerability_types,
            cwe_ids=prediction.cwe_ids,
            filename=request.filename or "snippet.c",
        )
    except FileNotFoundError as e:
        raise HTTPException(status_code=503, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error en predicción: {str(e)}")


@app.post("/scan")
def scan_files(request: ScanRequest):
    """
    Escanea múltiples archivos de código fuente y retorna un reporte completo.
    Equivalente al comando: python -m app.interfaces.cli scan <directorio>
    """
    if not request.files:
        raise HTTPException(status_code=400, detail="La lista 'files' no puede estar vacía.")

    try:
        use_case = _get_use_case()
        results = []
        vulnerable_count = 0

        for file_item in request.files:
            filename = file_item.get("filename", "unknown")
            code = file_item.get("code", "")

            if not code.strip():
                continue

            try:
                metrics = RawCodeModule(raw_code=code)
                prediction = use_case.execute(metrics)

                if prediction.is_vulnerable:
                    vulnerable_count += 1

                results.append({
                    "filename": filename,
                    "is_vulnerable": prediction.is_vulnerable,
                    "risk_probability": round(prediction.risk_probability, 4),
                    "risk_level": prediction.risk_level.value,
                    "vulnerability_types": prediction.vulnerability_types,
                    "cwe_ids": prediction.cwe_ids,
                    "recommendation": prediction.recommendation,
                })
            except Exception as e:
                results.append({
                    "filename": filename,
                    "error": str(e),
                    "is_vulnerable": False,
                    "risk_level": "UNKNOWN",
                })

        total = len(results)
        return {
            "summary": {
                "total_files": total,
                "vulnerable_files": vulnerable_count,
                "safe_files": total - vulnerable_count,
                "vulnerability_rate": round(vulnerable_count / total, 4) if total > 0 else 0,
            },
            "results": results,
        }
    except FileNotFoundError as e:
        raise HTTPException(status_code=503, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error en escaneo: {str(e)}")
