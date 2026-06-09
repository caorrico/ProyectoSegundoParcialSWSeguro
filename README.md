# SecureDataMining DevSecOps

Aplicacion academica en Python que usa mineria de datos para predecir si un modulo de
codigo presenta riesgo de vulnerabilidad. Implementa un clasificador Random Forest,
arquitectura en capas, principios SOLID y una base de integracion DevSecOps con GitHub
Actions.

## Requisitos

- Python 3.10 o superior
- `pip`

## Instalacion y ejecucion

```bash
python -m venv .venv
# Windows: .venv\Scripts\activate
# Linux/macOS: source .venv/bin/activate
python -m pip install -r requirements.txt

python scripts/generate_dataset.py
python -m app.interfaces.cli train
python -m app.interfaces.cli predict --input examples/sample_module_metrics.json
pytest
```

La prediccion imprime JSON con la clase, probabilidad, nivel de riesgo y recomendacion.
El modelo se guarda en `models/vulnerability_model.joblib` y las metricas de evaluacion
en `reports/metrics.json`.

## Metodologia SEMMA

1. **Sample:** `scripts/generate_dataset.py` crea 1500 registros sinteticos reproducibles.
2. **Explore:** la distribucion de clases y las importancias permiten observar patrones.
3. **Modify:** el entrenador valida columnas, valores faltantes y variable objetivo.
4. **Model:** `RandomForestTrainer` entrena un Random Forest con division estratificada.
5. **Assess:** se generan accuracy, precision, recall, F1, ROC-AUC, validacion cruzada,
   matriz de confusion e importancias de variables.

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

## Datos y seguridad

El dataset es sintetico y sirve para demostrar el flujo, no para evaluar codigo real en
produccion. Los archivos `.joblib` usan serializacion de Python: cargue unicamente
modelos generados por una fuente confiable.

Los niveles de riesgo son:

- `LOW`: probabilidad menor a `0.40`
- `MEDIUM`: probabilidad desde `0.40` y menor a `0.70`
- `HIGH`: probabilidad mayor o igual a `0.70`

## CI/CD

El workflow `.github/workflows/security-mining.yml` audita dependencias, ejecuta lint y
pruebas, genera el dataset, entrena el modelo y valida una prediccion en cada push o pull
request hacia `main`.
