# Agente experto para Codex: generar proyecto sólido y funcional

## Rol del agente

Actúa como un arquitecto senior de software, especialista en Python, minería de datos, desarrollo de software seguro, DevSecOps, arquitectura en capas, código limpio y principios SOLID.

Tu tarea es generar, completar o refactorizar un proyecto funcional llamado **SecureDataMining DevSecOps**, cuyo objetivo es aplicar minería de datos para predecir vulnerabilidades en módulos de código fuente.

## Contexto académico

El proyecto corresponde a la asignatura **Desarrollo de Software Seguro**. El tema central es la **Aplicación de Minería de Datos en el Desarrollo de Software Seguro**.

El sistema debe seguir la metodología **SEMMA**:

1. Sample: seleccionar o generar datos representativos.
2. Explore: analizar los datos.
3. Modify: limpiar y transformar datos.
4. Model: entrenar un modelo predictivo.
5. Assess: evaluar el modelo.

## Objetivo técnico

Construir una aplicación Python funcional que permita:

1. Generar un dataset sintético de métricas de código.
2. Entrenar un modelo de clasificación para detectar vulnerabilidades.
3. Guardar el modelo entrenado.
4. Ejecutar predicciones desde un archivo JSON.
5. Generar métricas de evaluación.
6. Ejecutar pruebas unitarias.
7. Integrarse con GitHub Actions como base de DevSecOps.

## Restricciones obligatorias

- Usar Python 3.10 o superior.
- Usar arquitectura en capas.
- Seguir principios SOLID.
- Aplicar código limpio.
- Evitar archivos enormes o innecesarios.
- No mezclar responsabilidades.
- No colocar lógica de machine learning dentro del CLI.
- No colocar lógica de infraestructura dentro del dominio.
- No hacer que el dominio dependa de pandas, sklearn, joblib o frameworks externos.
- Todo debe poder ejecutarse localmente con comandos simples.

## Arquitectura requerida

Genera o conserva esta estructura:

```text
secure_dm_codex_project/
├── app/
│   ├── domain/
│   │   ├── entities.py
│   │   ├── contracts.py
│   │   └── value_objects.py
│   ├── application/
│   │   └── use_cases/
│   │       ├── train_vulnerability_model.py
│   │       └── predict_vulnerability.py
│   ├── infrastructure/
│   │   ├── repositories/
│   │   │   └── csv_dataset_repository.py
│   │   └── ml/
│   │       ├── random_forest_trainer.py
│   │       └── random_forest_predictor.py
│   ├── interfaces/
│   │   ├── cli.py
│   │   └── dtos.py
│   └── shared/
│       └── settings.py
├── data/
│   ├── raw/
│   └── processed/
├── models/
├── reports/
├── scripts/
│   └── generate_dataset.py
├── examples/
│   └── sample_module_metrics.json
├── tests/
│   ├── test_entities.py
│   └── test_risk_level.py
├── .github/workflows/
│   └── security-mining.yml
├── requirements.txt
├── pyproject.toml
├── README.md
├── DIVISION_EQUITATIVA_EQUIPO.md
└── AGENTE_CODEX_EXPERTO.md
```

## Reglas de diseño SOLID

### Single Responsibility Principle

Cada clase debe tener una sola razón para cambiar.

Ejemplos:

- `CsvDatasetRepository`: solo carga y guarda datasets.
- `RandomForestTrainer`: solo entrena y evalúa el modelo.
- `RandomForestPredictor`: solo carga el modelo y predice.
- `TrainVulnerabilityModelUseCase`: solo coordina el entrenamiento.
- `PredictVulnerabilityUseCase`: solo coordina la predicción.

### Open/Closed Principle

El diseño debe permitir cambiar Random Forest por SVM, Decision Tree u otro algoritmo sin modificar el CLI ni los casos de uso.

### Liskov Substitution Principle

Cualquier implementación concreta debe poder reemplazar el contrato correspondiente sin romper el sistema.

### Interface Segregation Principle

Usar contratos pequeños:

- `DatasetRepository`
- `ModelTrainer`
- `ModelPredictor`

### Dependency Inversion Principle

Los casos de uso deben depender de contratos del dominio y no de clases concretas de infraestructura.

## Modelo de machine learning requerido

Usar **Random Forest Classifier** de scikit-learn.

Variables predictoras mínimas:

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

Variable objetivo:

- `is_vulnerable`

## Reglas para dataset sintético

El script `scripts/generate_dataset.py` debe crear un CSV en:

```text
data/raw/vulnerability_dataset.csv
```

Debe generar al menos 1000 registros.

La variable `is_vulnerable` debe calcularse con una lógica razonable, por ejemplo:

- Mayor complejidad aumenta riesgo.
- Más patrones inseguros aumenta riesgo.
- Más funciones deprecated aumenta riesgo.
- Menor cobertura de pruebas aumenta riesgo.
- Vulnerabilidades pasadas aumentan riesgo.

## Comandos obligatorios

El proyecto debe funcionar con estos comandos:

```bash
pip install -r requirements.txt
python scripts/generate_dataset.py
python -m app.interfaces.cli train
python -m app.interfaces.cli predict --input examples/sample_module_metrics.json
pytest
```

## Salida esperada de predicción

La predicción debe devolver una salida JSON similar a:

```json
{
  "is_vulnerable": true,
  "risk_probability": 0.82,
  "risk_level": "HIGH",
  "recommendation": "Revisar de forma prioritaria patrones inseguros, cobertura de pruebas y dependencias."
}
```

## Reglas de niveles de riesgo

- `LOW`: probabilidad menor a 0.40
- `MEDIUM`: probabilidad entre 0.40 y 0.70
- `HIGH`: probabilidad mayor o igual a 0.70

## Requisitos de evaluación

Guardar un archivo:

```text
reports/metrics.json
```

Debe contener:

- accuracy
- precision
- recall
- f1_score
- confusion_matrix
- feature_importances

## Requisitos de pruebas

Crear pruebas unitarias para:

1. Creación válida de `CodeModuleMetrics`.
2. Clasificación correcta de niveles de riesgo.
3. Validación de campos negativos o inválidos.

## Requisitos de CI/CD

Crear workflow en:

```text
.github/workflows/security-mining.yml
```

El workflow debe:

1. Instalar Python.
2. Instalar dependencias.
3. Ejecutar pruebas.
4. Generar dataset.
5. Entrenar modelo.
6. Ejecutar predicción de ejemplo.

## Instrucción final para Codex

Genera o completa todo el proyecto respetando exactamente esta arquitectura. Prioriza que el proyecto sea funcional, claro, mantenible y fácil de explicar en una defensa académica. No sobreingenierices. Usa nombres descriptivos, tipado, dataclasses, contratos con `Protocol`, manejo básico de errores y documentación suficiente.
