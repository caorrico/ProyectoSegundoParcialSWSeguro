# SecureDataMining DevSecOps

Proyecto academico de Desarrollo de Software Seguro que aplica mineria de datos
para detectar riesgo de vulnerabilidades en codigo fuente. El sistema usa modelos
clasicos de machine learning y analisis estatico; no depende de LLMs.

## Que hace

- Genera datasets sinteticos y datasets de entrenamiento basados en ejemplos OWASP.
- Entrena modelos de clasificacion para predecir codigo `SAFE` o `VULNERABLE`.
- Evalua el modelo y guarda metricas en `reports/metrics.json`.
- Predice riesgo desde metricas JSON o desde archivos de codigo fuente.
- Escanea directorios completos con codigo C/C++, Java, Python, JavaScript, TypeScript, Go y Rust.
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

Flujo principal con data real usando el notebook:

```bash
jupyter notebook notebooks/train_vulnerability_model.ipynb
```

Ese notebook limpia y combina datasets reales, entrena un pipeline con XGBoost,
evalua con holdout real por grupos, calibra el umbral de decision y guarda el
modelo final en `models/vulnerability_model.joblib`.

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

## Flujo del notebook con data real

El flujo principal de entrenamiento esta en
`notebooks/train_vulnerability_model.ipynb`. Esta ruta es la usada cuando se
quiere entrenar con datos reales y dejar un modelo listo para el CLI, la API y
los pipelines.

### 1. Configuracion

El notebook define:

- `TEST_SIZE = 0.25`: 25% de datos reales para prueba.
- `VALIDATION_SIZE = 0.20`: parte del entrenamiento real para calibrar umbral.
- `SYNTHETIC_SOURCES = {'owasp2025'}`: OWASP sintetico se excluye de la evaluacion.
- `FEATURE_COLUMNS = ['raw_code', 'language', 'source', 'code_length', 'line_count']`.
- `THRESHOLD_METRIC = 'accuracy'`: metrica usada para elegir el mejor umbral.
- `MIN_ACCURACY_TARGET = 0.82`: objetivo minimo de exactitud.
- `USE_AST_FEATURES = True`.
- `USE_SECURITY_PATTERN_FEATURES = True`.

### 2. Limpieza y combinacion de datasets

El notebook usa `build_clean_training_frame` para construir un dataset limpio y
unificado. El resultado se guarda en:

```text
data/processed/combined_clean_vulnerability_dataset.csv
```

La limpieza normaliza columnas, elimina duplicados por hash, conserva metadatos
como `source`, `language`, `group_id`, `code_hash`, `code_length` y `line_count`,
y deja una etiqueta binaria:

```text
is_vulnerable = 0 | 1
```

Puede cargar datasets reales disponibles localmente, incluyendo CVEFixes cuando
esta presente. Los ejemplos sinteticos OWASP pueden entrar al entrenamiento
final, pero no se usan como test real.

### 3. Split realista por grupos

El notebook separa datos reales y sinteticos:

```text
real_df      -> fuentes reales
synthetic_df -> OWASP sintetico
```

Luego usa `GroupShuffleSplit` con `group_id` o `code_hash`. Esto evita que dos
fragmentos relacionados o duplicados queden a la vez en entrenamiento y prueba.

La estrategia queda asi:

- `fit_df`: entrena un modelo temporal.
- `valid_df`: calibra el mejor umbral de decision.
- `train_real_df`: entrena el modelo evaluado.
- `test_df`: mide resultados finales solo con datos reales.

### 4. Extraccion de features

El notebook usa un `ColumnTransformer` que convierte codigo fuente y metadatos
en features numericas:

- `HashingVectorizer`: transforma `raw_code` en n-gramas de tokens de codigo.
- `ASTFeatureExtractor`: extrae estructura sintactica del codigo.
- `SecurityPatternFeatureExtractor`: cuenta patrones de seguridad y riesgo.
- `OneHotEncoder`: codifica `language` y `source`.
- `StandardScaler`: escala `code_length` y `line_count`.

Las features AST actuales son:

```text
ast_node_count
ast_max_depth
ast_pointer_ops
ast_function_calls
ast_loops
ast_if_statements
```

Las features de patrones de seguridad incluyen:

```text
security_lines_of_code
security_token_count
security_import_count
security_dangerous_total
security_sanitization_total
security_net_risk_patterns
security_dangerous_eval
security_dangerous_exec
security_dangerous_subprocess_shell
security_dangerous_os_system
security_dangerous_popen
security_dangerous_sql_raw
security_dangerous_pickle
security_dangerous_yaml_load
security_dangerous_unsafe_c
security_dangerous_hardcoded_secret
security_dangerous_taint_source_scanf
security_dangerous_taint_source_read
security_dangerous_taint_source_argv
security_dangerous_taint_source_getenv
security_sanitizer_parameterized_sql
security_sanitizer_escape
security_sanitizer_validation
security_sanitizer_shell_false
```

### 5. Modelo usado

El modelo del notebook es:

```text
XGBoost 300 balanced
```

Internamente usa `XGBClassifier` con:

```text
n_estimators=300
max_depth=8
learning_rate=0.1
subsample=0.8
colsample_bytree=0.8
scale_pos_weight=<balance seguro/vulnerable>
eval_metric=logloss
```

`scale_pos_weight` se calcula con la proporcion entre clases para compensar el
desbalance entre codigo seguro y vulnerable.

### 6. Calibracion del umbral

El modelo devuelve una probabilidad de vulnerabilidad con:

```python
pipeline.predict_proba(X)[:, 1]
```

El notebook no asume siempre `0.50`. Prueba umbrales de `0.05` a `0.95` y elige
`BEST_THRESHOLD` usando `accuracy`, con `f1` y `precision` como desempate.

La decision final es:

```python
is_vulnerable = probability >= BEST_THRESHOLD
```

### 7. Evaluacion

El notebook guarda y muestra:

- `accuracy`
- `precision`
- `recall`
- `f1_score`
- `roc_auc`
- matriz de confusion
- classification report
- metricas por lenguaje
- metricas por fuente
- curva ROC
- curva Precision-Recall
- accuracy por lenguaje
- validacion cruzada con `cv=3` en una muestra del `fit_df`

La estrategia de evaluacion registrada es:

```text
real_sources_group_holdout_with_validation_threshold
```

### 8. Guardado final

Despues de evaluar, el notebook reentrena el pipeline final con:

```text
train_real_df + synthetic_df
```

El objetivo es aprovechar mas datos para el artefacto final, pero manteniendo
una evaluacion honesta que ya se hizo sobre `test_df` real.

Artefactos generados:

```text
models/vulnerability_model.joblib
models/vectorizer.joblib
reports/metrics.json
reports/training_metadata.json
```

Ese `vulnerability_model.joblib` es el que luego usan:

- `python -m app.interfaces.cli predict --raw-code ...`
- `python -m app.interfaces.cli scan ...`
- `uvicorn app.interfaces.api:app ...`
- `.github/workflows/secure-pipeline.yml`

## Modelos y reportes

Los artefactos principales son:

- `models/vulnerability_model.joblib`: pipeline final del notebook o del CLI, usado por prediccion, API y pipeline.
- `models/vectorizer.joblib`: transformador de features del notebook cuando se entrena con codigo real.
- `reports/metrics.json`: metricas de evaluacion del entrenamiento, incluyendo threshold y holdout real cuando viene del notebook.
- `reports/pr_security_scan.json`: reporte generado por el pipeline para PRs.
- `reports/training_metadata.json`: perfil de datos, configuracion, fuentes, conteos y umbral del notebook.

Los modelos y reportes pesados pueden regenerarse y normalmente no deben
versionarse salvo que se decida publicarlos como artefactos de release.

## Tecnologias principales

- Python 3.10+
- scikit-learn, pipelines, `ColumnTransformer`, `HashingVectorizer`, `OneHotEncoder` y `StandardScaler`
- XGBoost como modelo principal del notebook con data real
- Random Forest para el flujo CLI base con dataset sintetico/OWASP
- LightGBM para experimentacion avanzada
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
