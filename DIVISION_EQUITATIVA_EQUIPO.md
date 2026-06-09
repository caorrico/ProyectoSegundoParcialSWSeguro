# División equitativa del proyecto para 3 personas

## Proyecto

**Aplicación de Minería de Datos en el Desarrollo de Software Seguro**

El proyecto consiste en desarrollar una solución funcional basada en minería de datos para predecir vulnerabilidades en módulos de software, siguiendo la metodología SEMMA y una arquitectura en capas con principios SOLID.

## Objetivo general del equipo

Construir un sistema funcional en Python que permita generar o cargar datos de métricas de código, entrenar un modelo predictivo de vulnerabilidades, evaluar sus resultados e integrarlo como base para un pipeline DevSecOps.

---

# Integrante 1: Arquitectura, dominio y documentación técnica

## Responsabilidad principal

Diseñar la arquitectura del proyecto, definir las entidades principales, contratos, estructura de carpetas y documentación técnica base.

## Actividades

1. Definir la arquitectura en capas:
   - `domain`
   - `application`
   - `infrastructure`
   - `interfaces`
   - `shared`

2. Crear las entidades del dominio:
   - Métricas del módulo de código.
   - Resultado de predicción.
   - Niveles de riesgo.

3. Crear contratos o interfaces:
   - Repositorio de dataset.
   - Servicio de entrenamiento.
   - Servicio de predicción.

4. Documentar el proyecto:
   - README principal.
   - Explicación de arquitectura.
   - Flujo SEMMA.
   - Instrucciones de instalación y ejecución.

5. Validar que el proyecto cumpla principios SOLID:
   - Separación de responsabilidades.
   - Dependencia de abstracciones.
   - Bajo acoplamiento entre capas.

## Entregables del integrante 1

- Estructura base del proyecto.
- Capa `domain` completa.
- Contratos principales.
- README técnico.
- Documento de arquitectura.

## Archivos principales asignados

```text
app/domain/entities.py
app/domain/contracts.py
app/domain/value_objects.py
app/shared/settings.py
README.md
DIVISION_EQUITATIVA_EQUIPO.md
```

---

# Integrante 2: Datos, SEMMA y entrenamiento del modelo

## Responsabilidad principal

Implementar el flujo de datos, la generación o carga del dataset, el preprocesamiento, el entrenamiento del modelo y la evaluación.

## Actividades

1. Implementar la fase Sample:
   - Generar dataset sintético inicial.
   - Permitir carga desde CSV.
   - Mantener estructura clara de datos.

2. Implementar la fase Explore:
   - Estadísticas descriptivas.
   - Distribución de clases vulnerable/no vulnerable.
   - Identificación de variables más relevantes.

3. Implementar la fase Modify:
   - Limpieza de datos.
   - Separación de variables predictoras y variable objetivo.
   - Validación de columnas obligatorias.

4. Implementar la fase Model:
   - Entrenar modelo Random Forest.
   - Guardar modelo en formato `.joblib`.
   - Mantener reproducibilidad con `random_state`.

5. Implementar la fase Assess:
   - Accuracy.
   - Precision.
   - Recall.
   - F1-score.
   - Matriz de confusión.
   - Reporte JSON.

## Entregables del integrante 2

- Dataset sintético funcional.
- Pipeline de entrenamiento.
- Modelo entrenado.
- Reporte de métricas.
- Script de generación de datos.

## Archivos principales asignados

```text
app/infrastructure/repositories/csv_dataset_repository.py
app/infrastructure/ml/random_forest_trainer.py
app/infrastructure/ml/random_forest_predictor.py
app/application/use_cases/train_vulnerability_model.py
scripts/generate_dataset.py
data/raw/vulnerability_dataset.csv
reports/metrics.json
models/vulnerability_model.joblib
```

---

# Integrante 3: Interfaz, predicción, pruebas e integración CI/CD

## Responsabilidad principal

Implementar la interfaz CLI, predicción de vulnerabilidades, pruebas automatizadas e integración con GitHub Actions.

## Actividades

1. Crear interfaz CLI:
   - Comando `train`.
   - Comando `predict`.
   - Lectura de archivo JSON.
   - Salida clara en consola.

2. Implementar caso de uso de predicción:
   - Cargar modelo entrenado.
   - Validar entrada.
   - Calcular probabilidad de riesgo.
   - Clasificar nivel de riesgo.
   - Generar recomendación.

3. Crear archivo de ejemplo:
   - Métricas de módulo vulnerable.
   - Formato JSON para pruebas rápidas.

4. Crear pruebas unitarias:
   - Validación de entidades.
   - Validación de niveles de riesgo.
   - Validación de predicción con mock o modelo entrenado.

5. Configurar CI/CD:
   - Instalar dependencias.
   - Ejecutar pruebas.
   - Generar dataset.
   - Entrenar modelo.
   - Ejecutar predicción de ejemplo.

## Entregables del integrante 3

- CLI funcional.
- Predicción desde JSON.
- Pruebas automatizadas.
- Workflow de GitHub Actions.
- Ejemplo de entrada.

## Archivos principales asignados

```text
app/interfaces/cli.py
app/interfaces/dtos.py
app/application/use_cases/predict_vulnerability.py
examples/sample_module_metrics.json
tests/test_risk_level.py
tests/test_entities.py
.github/workflows/security-mining.yml
```

---

# Cronograma sugerido

## Día 1: Base del proyecto

| Integrante | Actividad |
|---|---|
| Integrante 1 | Crear arquitectura, dominio y contratos |
| Integrante 2 | Crear dataset sintético y repositorio CSV |
| Integrante 3 | Crear CLI base y archivo JSON de ejemplo |

## Día 2: Modelo funcional

| Integrante | Actividad |
|---|---|
| Integrante 1 | Revisar dependencias entre capas y documentación |
| Integrante 2 | Entrenar Random Forest y generar métricas |
| Integrante 3 | Conectar CLI con entrenamiento y predicción |

## Día 3: Calidad e integración

| Integrante | Actividad |
|---|---|
| Integrante 1 | Validar SOLID y completar README |
| Integrante 2 | Mejorar evaluación y reporte |
| Integrante 3 | Crear pruebas y workflow CI/CD |

## Día 4: Entrega final

| Integrante | Actividad |
|---|---|
| Todos | Probar instalación desde cero |
| Todos | Ejecutar entrenamiento y predicción |
| Todos | Revisar documentación final |
| Todos | Preparar exposición o defensa técnica |

---

# Criterios de integración entre integrantes

1. Nadie debe modificar directamente la lógica asignada a otro integrante sin coordinar.
2. Toda clase nueva debe tener una responsabilidad clara.
3. La capa `domain` no debe importar librerías de infraestructura como pandas, sklearn o joblib.
4. La capa `application` debe depender de contratos, no de detalles técnicos.
5. La capa `infrastructure` puede usar pandas, sklearn, joblib y archivos.
6. La capa `interfaces` solo debe coordinar entrada/salida del usuario.
7. Todo cambio importante debe probarse con:

```bash
pytest
python scripts/generate_dataset.py
python -m app.interfaces.cli train
python -m app.interfaces.cli predict --input examples/sample_module_metrics.json
```

---

# Resultado esperado final

Al finalizar, el equipo debe entregar:

1. Proyecto Python funcional.
2. Arquitectura en capas.
3. Modelo Random Forest entrenable.
4. Predicción desde archivo JSON.
5. Dataset sintético inicial.
6. Reporte de métricas.
7. Pruebas unitarias.
8. Workflow CI/CD.
9. Documentación clara.
10. División equitativa de responsabilidades.
