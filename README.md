# SecureDataMining DevSecOps

Proyecto Python para analizar codigo fuente modificado en Pull Requests con un modelo clasico de mineria de datos. El flujo no usa LLMs: combina TF-IDF, features AST y reglas de seguridad para clasificar codigo como `SAFE` o `VULNERABLE` y automatizar un pipeline DevSecOps con GitHub Actions, Telegram, pruebas, merge y despliegue.

## Objetivo

- Entrenar un modelo tradicional para detectar patrones de vulnerabilidad en codigo fuente.
- Analizar los archivos modificados en un PR de `dev` hacia `test`.
- Bloquear el merge si el modelo detecta riesgo, comentar el PR, crear una issue, aplicar labels y notificar por Telegram.
- Si el codigo es seguro, ejecutar pruebas, mergear a `test`, mergear a `main`, construir Docker y disparar despliegue.

## Estructura

```text
.github/workflows/
└── secure-pipeline.yml         # Pipeline CI/CD (analisis ML, merge, deploy)
app/
├── domain/                     # Entidades, value objects y contratos sin dependencias ML
├── application/use_cases/      # Casos de uso de entrenamiento y prediccion
├── infrastructure/
│   ├── ml/                     # Entrenadores, predictor, AST y features de codigo
│   └── repositories/           # Carga de datasets sinteticos y reales
├── interfaces/                 # CLI, API FastAPI y Telegram
└── shared/                     # Settings
scripts/
├── analyze_pr_diff.py          # Analisis JSON de archivos modificados en PR
├── extract_code_features.py    # Extraccion local de features estaticas
├── generate_dataset.py         # Dataset sintetico numerico
├── generate_owasp_dataset.py   # Dataset OWASP 2025 de codigo fuente
└── send_telegram.py            # Notificaciones usando GitHub Secrets
notebooks/                      # Notebooks de entrenamiento con validacion cruzada
data/                           # Datasets generados y procesados
docs/informe/                   # Informe tecnico (LaTeX + PDF)
examples/                       # Codigo de ejemplo vulnerable y seguro
models/                         # Modelos entrenados (.joblib)
reports/                        # Metricas de evaluacion
tests/                          # Pruebas unitarias
Dockerfile                      # Imagen Docker para despliegue
render.yaml                     # Configuracion Render
requirements.txt                # Dependencias Python
pyproject.toml                  # Metadata del proyecto
README.md
```

## Instalacion

```bash
python -m venv .venv
# Windows:
.venv\Scripts\activate
# Linux/macOS:
# source .venv/bin/activate

python -m pip install --upgrade pip
python -m pip install -r requirements.txt
```

## Entrenar el modelo

Entrenamiento rapido con dataset OWASP local:

```bash
python scripts/generate_owasp_dataset.py
python -m app.interfaces.cli train --use-owasp
```

Entrenamiento con datasets reales disponibles:

```bash
python -m app.interfaces.cli train --use-combined
```

Notebook con combinacion, validacion cruzada y soporte CUDA:

```bash
jupyter notebook notebooks/train_vulnerability_model.ipynb
```

El notebook audita y limpia todas las fuentes locales que existan: `data/codexglue/*.jsonl`, `data/d2a/*.jsonl`, `data/reveal/*.jsonl`, `data/megavul/**/*.json`, `data/owasp2025/*.jsonl` y `data/data/CVEFixes.csv.zip`. No depende solamente de archivos `train.jsonl`; tambien usa `validation`, `test` y `dev` cuando son los splits disponibles.

Por defecto `MAX_RECORDS_PER_SOURCE = None`, asi que usa todos los registros utilizables. Si quieres una corrida rapida de prueba puedes cambiar temporalmente ese valor en la primera celda.

El notebook entrena desde cero: elimina los artefactos anteriores antes de ejecutar, limpia marcadores obvios como comentarios `SAFE:` / `VULNERABLE:`, crea un holdout de evaluacion con datasets reales y separa por `group_id` para reducir fuga entre pares vulnerable/fixed. OWASP sintetico puede apoyar el entrenamiento, pero no se usa como test.

Para evitar sesgo hacia la clase mayoritaria, el notebook balancea los datos usados en entrenamiento con submuestreo controlado de la clase mayoritaria hasta una relacion 1:1 entre `safe` y `vulnerable`. El test real no se balancea, porque debe conservar su distribucion natural para que las metricas no queden maquilladas.

El notebook detecta CUDA con `nvidia-smi`. Si CUDA esta disponible y `xgboost` puede usarla, entrena con `device="cuda"`; si no, continua en CPU. Tambien guarda un dataset limpio combinado en `data/processed/` y muestra graficas de distribucion, matriz de confusion, curva ROC, precision-recall, metricas principales e importancia de features. Los artefactos se guardan en:

- `models/vulnerability_model.joblib`
- `models/vectorizer.joblib`
- `reports/metrics.json`
- `reports/training_metadata.json`

## Prediccion local

Con codigo vulnerable:

```bash
python -m app.interfaces.cli predict --raw-code examples/vulnerable_sample.cpp
```

Con codigo seguro:

```bash
python -m app.interfaces.cli predict --raw-code examples/safe_sample.cpp
```

Extraer features estaticas:

```bash
python scripts/extract_code_features.py examples/vulnerable_sample.cpp
```

Analizar cambios como lo hace el pipeline:

```bash
git diff --name-only test...HEAD > changed_files.txt
python scripts/analyze_pr_diff.py --changed-files changed_files.txt --output reports/pr_security_scan.json
```

La salida JSON contiene:

```json
{
  "status": "VULNERABLE",
  "probability": 0.91,
  "details": "1 vulnerable file(s) found out of 1 analyzed.",
  "files": []
}
```

## Features del modelo

El pipeline de entrenamiento usa:

- tokens de codigo con `TfidfVectorizer`
- estructura AST simplificada con `tree-sitter`
- profundidad y cantidad de nodos AST
- llamadas a funciones
- imports/includes
- llamadas peligrosas como `eval`, `exec`, `subprocess(..., shell=True)`, `os.system`, `system`, `pickle.load`, `yaml.load`
- patrones de SQL raw, command injection, hardcoded secrets y funciones inseguras de C/C++
- presencia de sanitizacion, escape o validacion

## API y Docker

Ejecutar API local:

```bash
uvicorn app.interfaces.api:app --host 0.0.0.0 --port 8000
```

Endpoints principales:

- `GET /health`
- `POST /predict`
- `POST /scan`

Construir imagen:

```bash
docker build -t secure-datamining-api .
```

## Pipeline CI/CD

Workflow principal:

```text
.github/workflows/secure-pipeline.yml
```

Se activa con Pull Requests hacia `test`, por ejemplo `dev -> test`.

Fases:

1. Notifica inicio por Telegram.
2. Instala dependencias y prepara el modelo si no existe.
3. Detecta archivos modificados.
4. Ejecuta `scripts/analyze_pr_diff.py`.
5. Si el resultado es `VULNERABLE`, falla el job, comenta el PR, crea issue, aplica `fixing-required` y notifica.
6. Si el resultado es `SAFE`, comenta el PR, aplica `security-approved`, notifica y ejecuta pruebas.
7. Si las pruebas pasan, mergea el PR a `test`.
8. Mergea `test` hacia `main`, construye Docker y dispara deploy en Render si existe hook.

## Secrets requeridos

Configurar en GitHub: `Settings -> Secrets and variables -> Actions`.

- `TELEGRAM_BOT_TOKEN`: token del bot de Telegram.
- `TELEGRAM_CHAT_ID`: chat o grupo destino.
- `RENDER_DEPLOY_HOOK_URL`: opcional, hook de despliegue de Render.
- `PRODUCTION_URL`: opcional, URL final de produccion para documentacion/notificaciones.

El workflow usa `GITHUB_TOKEN` para comentar PRs, crear issues, aplicar labels y mergear. Si la organizacion bloquea merges con `GITHUB_TOKEN`, crear un PAT con permisos de repo y adaptar el checkout/merge para usar ese secret.

## Configurar Telegram

Puedes obtener el `chat_id` con:

```bash
python scripts/setup_telegram.py --token <TOKEN_DEL_BOT>
```

No hardcodees secretos en el repositorio. En local puedes exportarlos como variables de entorno para probar:

```bash
set TELEGRAM_BOT_TOKEN=<token>
set TELEGRAM_CHAT_ID=<chat_id>
python scripts/send_telegram.py --message "Prueba SecureDataMining"
```

## Branch Protection

Configurar reglas en GitHub:

1. Proteger `test`.
2. Proteger `main`.
3. Requerir que el workflow `Secure ML CI/CD Pipeline` pase antes de mergear.
4. Bloquear push directo a `main`.
5. Permitir merge automatico solo si los checks estan en verde.

## Validacion local

```bash
python -m pytest -q
python scripts/generate_owasp_dataset.py
python -m app.interfaces.cli train --use-owasp
python -m app.interfaces.cli predict --raw-code examples/vulnerable_sample.cpp
python scripts/analyze_pr_diff.py --changed-files changed_files.txt
```

## Despliegue

El repo incluye `Dockerfile` y `render.yaml`. En Render:

1. Crear un Web Service conectado al repositorio.
2. Configurar build/deploy con Docker.
3. Copiar el Deploy Hook en `RENDER_DEPLOY_HOOK_URL`.
4. Configurar `PRODUCTION_URL` con la URL publica.

## Notas de versionado

Los modelos, reportes y datasets grandes estan ignorados por Git porque se regeneran con scripts o notebook. Si se necesita publicar un modelo entrenado, subirlo como release artifact o ajustar conscientemente `.gitignore`.
