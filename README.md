# SecureDataMining DevSecOps

Aplicacion en Python orientada a DevSecOps que utiliza mineria de datos y Machine Learning avanzado para predecir vulnerabilidades en modulos de codigo fuente (C, C++, Java). 

El sistema implementa una arquitectura en capas, extracción sintáctica y estructural (AST mediante `tree-sitter`), optimización de hiperparámetros automatizada y explicabilidad de modelos con SHAP.

## Requisitos

- Python 3.10 o superior
- `pip`

## Instalacion y ejecucion

```bash
python -m venv .venv
# Windows: .venv\Scripts\activate
# Linux/macOS: source .venv/bin/activate
python -m pip install -r requirements.txt

# Entrenar con el dataset sintético por defecto
python -m app.interfaces.cli train

# Entrenar el modelo con multiples datasets reales combinados
python -m app.interfaces.cli train --use-combined

# Entrenar el modelo buscando automaticamente los mejores hiperparametros (demora mas)
python -m app.interfaces.cli train --use-combined --tune

# Predecir riesgo desde codigo fuente puro generando un reporte visual SHAP
python -m app.interfaces.cli predict --raw-code examples/vulnerable_sample.cpp --shap-report reports/shap_cpp_sample.html
```

La prediccion imprime JSON con la clase, probabilidad, nivel de riesgo y recomendacion.
El modelo se guarda en `models/vulnerability_model.joblib` y las metricas de evaluacion
en `reports/metrics.json`.

## Datasets Reales Soportados

El proyecto fue reestructurado para entrenar contra datasets de nivel de producción que agrupan miles de módulos C/C++ y Java:

- **MegaVul** (C/C++ y Java)
- **CodeXGLUE / Devign**
- **D2A** (IBM)
- **ReVeal** (Chromium / Debian)
- **VulBERTa** (Imperial College London)

Puede entrenar con cualquier combinación usando los argumentos `--use-reveal`, `--use-d2a`, `--use-vulberta`, `--use-codexglue`, o utilizarlos todos a la vez con `--use-combined`.

## Extracción de Características (Pipeline)

El modelo cuenta con un pipeline híbrido inteligente que fusiona:
1. **Sintaxis (TF-IDF):** Extracción de tokens clave (hasta 1000 features).
2. **Estructura (AST Extractor):** Usando el compilador `tree-sitter`, se parsea el código fuente y se extraen métricas semánticas como profundidad del árbol, llamadas a funciones, operaciones de punteros y complejidad ciclomática.

## Modelos y Benchmarking

La infraestructura soporta múltiples algoritmos evaluados bajo una validación cruzada rigurosa:
- **Random Forest (Modelo Principal Optimizado)**
- **XGBoost**
- **LightGBM**
- **SVM**

Puedes ejecutar el script de prueba para compararlos tú mismo: `python scripts/benchmark_models.py`

## Arquitectura

```text
app/
|-- domain/          # Entidades, objetos de valor y contratos sin frameworks externos
|-- application/     # Casos de uso que dependen de contratos
|-- infrastructure/  # CSV, pandas, scikit-learn y persistencia del modelo
|-- interfaces/      # CLI y DTO de entrada
`-- shared/          # Configuracion de rutas
```

La infraestructura puede reemplazar el algoritmo o repositorio sin cambiar los casos de
uso. El CLI solamente compone dependencias y gestiona entrada/salida.

## Explicabilidad y Seguridad

El CLI provee reportes **SHAP** en formato HTML (`--shap-report`). En vez de ser una "caja negra", el modelo indica visualmente y numéricamente qué variables (por ejemplo, el exceso de punteros o ciertas librerías en el TF-IDF) inclinan la balanza hacia la clasificación "vulnerable".

Los archivos `.joblib` generados durante el entrenamiento usan serialización nativa y rápida: cargue únicamente modelos generados internamente por el propio sistema.

Los niveles de riesgo son:

- `LOW`: probabilidad menor a `0.40`
- `MEDIUM`: probabilidad desde `0.40` y menor a `0.70`
- `HIGH`: probabilidad mayor o igual a `0.70`

## CI/CD

El workflow `.github/workflows/security-mining.yml` audita dependencias, ejecuta lint y
pruebas, genera el dataset, entrena el modelo y valida una prediccion en cada push o pull
request hacia `main`.
