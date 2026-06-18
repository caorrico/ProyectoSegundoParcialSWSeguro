# SecureDataMining DevSecOps

Proyecto academico de Desarrollo de Software Seguro que aplica mineria de datos
para detectar riesgo de vulnerabilidades en codigo fuente. El sistema usa modelos
clasicos de machine learning y analisis estatico; no depende de LLMs.

## Que hace

- Genera datasets sinteticos y datasets de entrenamiento basados en ejemplos OWASP.
- Entrena modelos de clasificacion para predecir codigo `SAFE` o `VULNERABLE`.
- Evalua el modelo y guarda metricas en `reports/metrics.json`.
- Predice riesgo desde metricas JSON o desde archivos de codigo fuente.
- Escanea directorios completos con codigo C/C++, Java.
- Expone una API FastAPI lista para Docker y Render.
- Automatiza revision de seguridad en Pull Requests con GitHub Actions.
- Notifica resultados por Telegram cuando los secrets estan configurados.

## Arquitectura

```text
app/
|-- domain/                       # Entidades, value objects y contratos sin frameworks ML
|-- application/use_cases/        # Casos de uso de entrenamiento y prediccion
|-- infrastructure/ml/            # Entrenadores, predictores y extraccion de features
|-- infrastructure/repositories/  # Lectura de datasets sinteticos y reales
|-- interfaces/                   # CLI, DTOs, API FastAPI y Telegram
|-- shared/                       # Configuracion de rutas y parametros globales
scripts/                         # Automatizaciones de dataset, entrenamiento, CI y analisis
examples/                        # Codigo vulnerable/seguro y ejemplos para prediccion
tests/                           # Pruebas unitarias
.github/workflows/               # Pipelines DevSecOps
docs/                            # Documentacion tecnica
```

La separacion sigue SOLID: el dominio no importa `pandas`, `sklearn`, `joblib`
ni FastAPI; esas dependencias viven en infraestructura e interfaces.

## Instalacion local

```bash
python -m venv .venv
.venv\Scripts\activate
python -m pip install --upgrade pip
python -m pip install -r requirements.txt
```

En PowerShell, si `npm.ps1` u otros scripts tienen restricciones de ejecucion,
usa los ejecutables `.cmd` equivalentes cuando aplique. Este proyecto principal
es Python.

## Uso rapido

Entrenar con dataset sintetico numerico:

```bash
python scripts/generate_dataset.py
python -m app.interfaces.cli train
```

Entrenar con dataset OWASP local:

```bash
python scripts/generate_owasp_dataset.py
python -m app.interfaces.cli train --use-owasp
```

Predecir desde metricas JSON:

```bash
python -m app.interfaces.cli predict --input examples/sample_module_metrics.json
```

Predecir desde codigo fuente:

```bash
python -m app.interfaces.cli predict --raw-code examples/vulnerable_sample.cpp
python -m app.interfaces.cli predict --raw-code examples/safe_sample.cpp
```

Escanear un directorio completo:

```bash
python -m app.interfaces.cli scan examples
```

Ejecutar validaciones:

```bash
python -m ruff check .
python -m pytest -q
python -m pip check
python -m pip_audit -r requirements.txt
```

## Modelos y reportes

Los artefactos principales son:

- `models/vulnerability_model.joblib`: modelo usado por el CLI y la API.
- `reports/metrics.json`: metricas de evaluacion del entrenamiento.
- `reports/pr_security_scan.json`: reporte generado por el pipeline para PRs.
- `reports/training_metadata.json`: metadata cuando se ejecuta entrenamiento avanzado.

Los modelos y reportes pesados pueden regenerarse y normalmente no deben
versionarse salvo que se decida publicarlos como artefactos de release.

## Tecnologias principales

- Python 3.10+
- scikit-learn, Random Forest, TF-IDF y pipelines de features
- XGBoost y LightGBM para experimentacion avanzada
- pandas, numpy, scipy y joblib
- tree-sitter para features AST de C/C++ y Java
- SHAP para explicabilidad local del modelo
- FastAPI y Uvicorn para la API
- Docker y Render para despliegue
- pytest, ruff, pip-audit y GitHub Actions para DevSecOps
- Telegram Bot API para notificaciones del pipeline

La explicacion completa esta en
[`docs/TECNOLOGIAS_PIPELINE.md`](docs/TECNOLOGIAS_PIPELINE.md).

## API y Docker

Ejecutar API local:

```bash
uvicorn app.interfaces.api:app --host 0.0.0.0 --port 8000
```

Endpoints:

- `GET /health`: estado del servicio y disponibilidad del modelo.
- `POST /predict`: prediccion de un fragmento de codigo.
- `POST /scan`: escaneo de varios archivos enviados en JSON.

Construir imagen:

```bash
docker build -t secure-datamining-api .
```

El despliegue en Render esta descrito en `render.yaml`.

## Pipelines

El repositorio contiene dos workflows:

- `.github/workflows/secure-pipeline.yml`: pipeline DevSecOps principal para PRs hacia `test`. Ejecuta lint, pruebas, prepara modelo si hace falta, analiza archivos modificados, comenta el PR, aplica labels, bloquea codigo vulnerable, mergea a `test` si todo pasa y luego mergea a `main`, construye Docker y dispara Render.
- `.github/workflows/security-mining.yml`: workflow alternativo de inferencia de seguridad para PRs hacia `test`. Ejecuta `scripts/ci_inference_pipeline.py`, genera `security_report.json`, comenta resultados y bloquea cuando detecta vulnerabilidad.

Secrets recomendados en GitHub Actions:

- `TELEGRAM_BOT_TOKEN`
- `TELEGRAM_CHAT_ID`
- `RENDER_DEPLOY_HOOK_URL`
- `PRODUCTION_URL`

## Flujo de ramas recomendado

1. Trabajar cambios en `dev` o una rama feature.
2. Crear Pull Request hacia `test`.
3. Dejar que GitHub Actions ejecute revision de seguridad y pruebas.
4. Si el resultado es vulnerable, corregir y actualizar el PR.
5. Si el resultado es seguro, el pipeline puede mergear a `test`.
6. Luego el pipeline mergea `test` hacia `main`, construye Docker y despliega.

## Notas de seguridad

- No guardar tokens ni credenciales en el repositorio.
- Mantener los secrets en GitHub Actions o variables de entorno locales.
- Revisar `pip-audit` antes de entregar o desplegar.
- Reentrenar el modelo cuando cambien datasets, features o umbrales.
