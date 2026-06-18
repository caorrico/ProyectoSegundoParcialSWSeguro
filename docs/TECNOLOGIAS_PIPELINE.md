# Documento tecnico: tecnologias, funcionamiento y pipeline

## 1. Vision general

SecureDataMining DevSecOps es un proyecto Python que usa mineria de datos para
predecir si un modulo de codigo fuente tiene riesgo de vulnerabilidades. La
idea central es convertir codigo o metricas de codigo en features, entrenar un
modelo clasico de machine learning y usar ese modelo dentro de un flujo
DevSecOps automatizado.

El proyecto no usa LLMs. La deteccion se apoya en:

- Features numericas de complejidad y calidad.
- Tokens de codigo con TF-IDF.
- Features de estructura AST con tree-sitter.
- Reglas de seguridad para patrones peligrosos.
- Modelos clasicos como Random Forest y XGBoost.

## 2. Tecnologias usadas

### Python 3.10+

Es el lenguaje base del proyecto. Se usa para la aplicacion, scripts de
entrenamiento, CLI, API, pruebas y automatizaciones del pipeline.

### pandas y numpy

Se usan para preparar datasets, cargar registros, transformar columnas y manejar
matrices o arreglos numericos antes de entrenar.

### scikit-learn

Es la libreria principal de machine learning. En el flujo base se usa
`RandomForestClassifier`, `train_test_split`, metricas de evaluacion,
`TfidfVectorizer`, `FeatureUnion` y pipelines de features.

### XGBoost y LightGBM

Estan disponibles para experimentos avanzados de clasificacion. El script
`scripts/final_training_pipeline.py` usa XGBoost para un entrenamiento de mayor
precision cuando existen datos reales suficientes.

### scipy

Permite combinar matrices dispersas generadas por TF-IDF, AST y metricas de
codigo.

### joblib

Guarda y carga modelos entrenados en archivos `.joblib`, por ejemplo
`models/vulnerability_model.joblib`.

### tree-sitter

Extrae informacion estructural del codigo, especialmente para C/C++ y Java.
Permite representar caracteristicas del arbol sintactico sin ejecutar el codigo.

### SHAP

Se usa para explicabilidad. El predictor puede generar un reporte HTML con las
features que mas influyeron en una prediccion.

### FastAPI y Uvicorn

Exponen el modelo como API HTTP. FastAPI define los endpoints y Uvicorn levanta
el servidor local o dentro de Docker.

### Docker

Empaqueta la API para desplegarla de forma reproducible. El `Dockerfile`
instala dependencias y ejecuta la aplicacion.

### Render

El archivo `render.yaml` describe un Web Service Docker con health check en
`/health`. El pipeline puede disparar deploy con `RENDER_DEPLOY_HOOK_URL`.

### pytest

Ejecuta pruebas unitarias sobre entidades, DTOs, casos de uso y niveles de
riesgo.

### ruff

Valida estilo y errores estaticos de Python antes de aceptar cambios.

### pip-audit

Audita vulnerabilidades conocidas en dependencias de `requirements.txt`.

### GitHub Actions

Automatiza revision de seguridad, pruebas, merge controlado, construccion Docker
y despliegue.

### Telegram Bot API

Envia notificaciones del pipeline cuando existen los secrets
`TELEGRAM_BOT_TOKEN` y `TELEGRAM_CHAT_ID`.

## 3. Arquitectura del proyecto

El proyecto esta dividido en capas:

### Dominio

Ruta: `app/domain/`

Contiene entidades, value objects y contratos. Esta capa representa las reglas
del negocio y no depende de frameworks externos de ML, API o persistencia.

Elementos importantes:

- `entities.py`: modelos como `CodeModuleMetrics` y `RawCodeModule`.
- `value_objects.py`: niveles de riesgo y valores derivados.
- `contracts.py`: protocolos para repositorios, entrenadores y predictores.

### Aplicacion

Ruta: `app/application/use_cases/`

Coordina los casos de uso. No entrena directamente ni lee archivos por si sola;
recibe contratos y delega a infraestructura.

Casos principales:

- `TrainVulnerabilityModelUseCase`: carga datos y entrena.
- `PredictVulnerabilityUseCase`: recibe metricas o codigo y retorna prediccion.

### Infraestructura

Ruta: `app/infrastructure/`

Implementa detalles tecnicos:

- Repositorios de datasets CSV, OWASP, CodeXGLUE, D2A, ReVeal, CVEFixes,
  MegaVul y combinados.
- Entrenadores y predictores ML.
- Extraccion AST, TF-IDF, metricas de codigo y patrones sospechosos.

### Interfaces

Ruta: `app/interfaces/`

Expone el sistema hacia fuera:

- `cli.py`: comandos `train`, `predict` y `scan`.
- `api.py`: endpoints FastAPI.
- `dtos.py`: validacion de datos de entrada.
- `telegram.py`: soporte para notificaciones.

### Shared

Ruta: `app/shared/settings.py`

Centraliza rutas y parametros:

- Dataset base: `data/raw/vulnerability_dataset.csv`.
- Modelo base: `models/vulnerability_model.joblib`.
- Reporte de metricas: `reports/metrics.json`.
- Semilla y proporcion de test.

## 4. Funcionamiento paso a paso

### Paso 1: instalar dependencias

```bash
python -m venv .venv
.venv\Scripts\activate
python -m pip install --upgrade pip
python -m pip install -r requirements.txt
```

### Paso 2: generar datos

Para el flujo base:

```bash
python scripts/generate_dataset.py
```

Este script crea `data/raw/vulnerability_dataset.csv` con metricas como lineas
de codigo, complejidad ciclomatica, profundidad, dependencias, patrones
inseguros, cobertura de pruebas y vulnerabilidades pasadas.

Para ejemplos de codigo OWASP:

```bash
python scripts/generate_owasp_dataset.py
```

Este script prepara registros de codigo vulnerable y seguro para entrenar con
`--use-owasp`.

### Paso 3: entrenar modelo

Entrenamiento base:

```bash
python -m app.interfaces.cli train
```

Entrenamiento con OWASP:

```bash
python -m app.interfaces.cli train --use-owasp
```

El CLI construye el caso de uso de entrenamiento, selecciona el repositorio de
datos y usa un entrenador. Al final guarda:

- `models/vulnerability_model.joblib`
- `reports/metrics.json`

### Paso 4: evaluar resultados

El reporte de metricas incluye datos como:

- accuracy
- precision
- recall
- f1_score
- matriz de confusion
- importancia de features

Estas metricas permiten explicar si el modelo esta clasificando correctamente
codigo seguro y vulnerable.

### Paso 5: predecir desde JSON

```bash
python -m app.interfaces.cli predict --input examples/sample_module_metrics.json
```

El JSON contiene metricas numericas. El sistema las valida, arma un objeto de
dominio, carga el modelo y devuelve un resultado similar a:

```json
{
  "is_vulnerable": true,
  "risk_probability": 0.82,
  "risk_level": "HIGH",
  "recommendation": "Revisar patrones inseguros, cobertura y dependencias."
}
```

### Paso 6: predecir desde codigo fuente

```bash
python -m app.interfaces.cli predict --raw-code examples/vulnerable_sample.cpp
```

El predictor detecta el lenguaje, extrae features del codigo, calcula
probabilidad de vulnerabilidad y clasifica el riesgo.

### Paso 7: escanear un directorio

```bash
python -m app.interfaces.cli scan examples
```

El CLI busca archivos fuente, predice cada archivo y guarda un reporte
`vulnerability_scan_report.json` dentro del directorio analizado.

### Paso 8: ejecutar API

```bash
uvicorn app.interfaces.api:app --host 0.0.0.0 --port 8000
```

Endpoints:

- `GET /health`: confirma si el servicio esta activo y si el modelo existe.
- `POST /predict`: recibe un fragmento de codigo.
- `POST /scan`: recibe varios archivos en un JSON.

### Paso 9: construir Docker

```bash
docker build -t secure-datamining-api .
```

La imagen permite ejecutar la API en ambientes reproducibles.

## 5. Como funciona el modelo

El sistema puede trabajar con dos tipos de entrada:

### Entrada de metricas

Usa columnas numericas como:

- `lines_of_code`
- `cyclomatic_complexity`
- `nesting_depth`
- `dependency_count`
- `deprecated_functions`
- `unsafe_patterns`
- `security_hotspots`
- `test_coverage`
- `recent_commits`
- `past_vulnerabilities`

Con esas columnas se entrena un clasificador y se calcula la probabilidad de que
el modulo sea vulnerable.

### Entrada de codigo fuente

Usa una combinacion de:

- TF-IDF sobre tokens del codigo.
- Features AST.
- Conteo de llamadas peligrosas.
- Patrones de inyeccion, buffer overflow, secretos hardcodeados y funciones
  inseguras.
- Indicadores de sanitizacion o validacion.

El resultado final es:

- `is_vulnerable`: booleano.
- `risk_probability`: probabilidad de riesgo.
- `risk_level`: `LOW`, `MEDIUM` o `HIGH`.
- `recommendation`: recomendacion tecnica.
- `vulnerability_types` y `cwe_ids` cuando aplican.

## 6. Pipeline DevSecOps principal

Archivo: `.github/workflows/secure-pipeline.yml`

Se ejecuta cuando hay Pull Request hacia la rama `test`.

### Job 1: `security-review`

1. Descarga el repositorio.
2. Configura Python 3.10.
3. Instala dependencias.
4. Ejecuta `ruff` y `pytest`.
5. Notifica inicio por Telegram.
6. Prepara el modelo si no existe:

```bash
python scripts/generate_owasp_dataset.py
python -m app.interfaces.cli train --use-owasp
```

7. Detecta archivos modificados contra la rama base.
8. Ejecuta:

```bash
python scripts/analyze_pr_diff.py --changed-files /tmp/changed_files.txt --output reports/pr_security_scan.json
```

9. Sube el reporte como artefacto.
10. Si el resultado es `SAFE`, comenta el PR y agrega `security-approved`.
11. Si el resultado es `VULNERABLE`, comenta el PR, agrega `fixing-required`,
    crea una issue y bloquea el merge.

### Job 2: `tests-and-merge-test`

Solo corre si el analisis de seguridad fue `SAFE`.

1. Descarga el repo.
2. Instala dependencias.
3. Ejecuta pruebas.
4. Mergea el Pull Request hacia `test`.
5. Notifica el merge por Telegram.

### Job 3: `merge-main-and-deploy`

Solo corre si el merge a `test` fue exitoso.

1. Hace checkout de `main`.
2. Mergea `origin/test` hacia `main`.
3. Hace push a `main`.
4. Construye imagen Docker.
5. Si existe `RENDER_DEPLOY_HOOK_URL`, dispara deploy en Render.
6. Notifica el resultado.

## 7. Workflow alternativo de inferencia

Archivo: `.github/workflows/security-mining.yml`

Tambien se ejecuta en Pull Requests hacia `test`. Su flujo es mas directo:

1. Instala dependencias.
2. Notifica inicio por Telegram.
3. Ejecuta `scripts/ci_inference_pipeline.py` sobre un archivo de ejemplo.
4. Genera `security_report.json`.
5. Si detecta vulnerabilidad, comenta el PR, aplica `fixing-required` y falla.

Este workflow depende del modelo esperado por `scripts/ci_inference_pipeline.py`
en `models/modelo_final_cvefixes.joblib`. El pipeline principal usa el modelo
base del proyecto en `models/vulnerability_model.joblib`.

## 8. Secrets necesarios

Configurar en GitHub:

- `TELEGRAM_BOT_TOKEN`: token del bot.
- `TELEGRAM_CHAT_ID`: chat o grupo de destino.
- `RENDER_DEPLOY_HOOK_URL`: hook opcional de Render.
- `PRODUCTION_URL`: URL publica opcional para mensajes o documentacion.

El `GITHUB_TOKEN` lo provee GitHub Actions y se usa para comentar PRs, crear
issues, aplicar labels y hacer merges.

## 9. Validacion recomendada antes de entregar

```bash
python -m ruff check .
python -m pytest -q
python scripts/generate_dataset.py
python -m app.interfaces.cli train
python -m app.interfaces.cli predict --input examples/sample_module_metrics.json
python scripts/generate_owasp_dataset.py
python -m app.interfaces.cli train --use-owasp
python -m app.interfaces.cli predict --raw-code examples/vulnerable_sample.cpp
python -m pip check
python -m pip_audit -r requirements.txt
```

## 10. Resumen para defensa

El proyecto implementa una arquitectura por capas con dominio limpio,
entrenamiento ML reproducible, prediccion local por CLI, API HTTP, Docker,
despliegue en Render y pipelines GitHub Actions. El flujo DevSecOps revisa PRs
antes de mergear, bloquea codigo vulnerable, registra evidencias en reportes,
notifica por Telegram y automatiza el camino desde `test` hasta `main` y
despliegue.
