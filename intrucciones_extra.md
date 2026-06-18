Actúa como un desarrollador senior especializado en Python, Machine Learning, CI/CD, GitHub Actions, seguridad de software y DevSecOps.

Necesito que revises TODO el código existente de este proyecto antes de hacer cambios. La idea principal NO es crear todo desde cero, sino adaptar, corregir, ordenar y mejorar lo que ya existe para cumplir con los siguientes requerimientos del proyecto.

Contexto del proyecto:
Debo implementar un pipeline CI/CD seguro que analice código fuente modificado en un Pull Request usando un modelo de minería de datos tradicional. No se permite usar LLM. El modelo debe clasificar código como SEGURO o VULNERABLE. Si el código es vulnerable, el pipeline debe bloquear el merge, comentar el PR, crear una issue, aplicar una etiqueta y notificar por Telegram. Si es seguro, debe continuar con pruebas, merge a test, merge a main y despliegue.

Tareas principales:

1. Revisar el proyecto actual

* Analiza la estructura completa del repositorio.
* Identifica qué código ya existe para entrenamiento, extracción de features, modelo, análisis de código, pipeline, notificaciones y despliegue.
* Reutiliza y adapta el código existente siempre que sea posible.
* No elimines código útil sin razón.
* Corrige errores, rutas, imports, nombres de archivos y estructura si es necesario.
* Deja el proyecto ordenado y fácil de ejecutar.

2. Condensar el entrenamiento del modelo en un Notebook de Jupyter

* Crea o adapta un notebook llamado, por ejemplo:
  notebooks/train_vulnerability_model.ipynb
* El notebook debe entrenar el modelo usando TODOS los datasets existentes en el proyecto de manera combinada.
* Si los datasets tienen formatos diferentes, unifícalos en una sola estructura de entrenamiento.
* El notebook debe incluir:
  * carga de datasets
  * limpieza de datos
  * combinación de datasets
  * extracción de features
  * separación train/test
  * validación cruzada
  * entrenamiento final
  * métricas como accuracy, precision, recall, f1-score y matriz de confusión
  * guardado del modelo entrenado en formato .joblib o .pkl
* El modelo debe ser de minería de datos tradicional, por ejemplo:
  * RandomForest
  * XGBoost
  * SVM
  * Logistic Regression
  * Gradient Boosting
  * u otro modelo clásico válido
* No uses GPT, Claude, Llama, CodeLlama ni ningún LLM.

3. Uso de GPU / CUDA

* Adapta el entrenamiento para aprovechar la GPU de mi computadora cuando sea posible.
* Implementa soporte CUDA correctamente.
* Si el modelo elegido no soporta GPU directamente, usa una alternativa compatible, por ejemplo:
  * XGBoost con GPU
  * RAPIDS cuML si aplica
  * PyTorch solo si se usa como parte auxiliar y no como LLM
* El código debe detectar si CUDA está disponible.
* Si CUDA no está disponible, debe continuar entrenando en CPU sin romperse.
* Corrige cualquier referencia incorrecta a “kuda”; debe ser “CUDA”.

4. Features mínimas obligatorias
   El modelo debe extraer características del código fuente como mínimo:

* tokens del código
* profundidad o estructura simplificada del AST
* llamadas a funciones peligrosas como eval, exec, subprocess, os.system, SQL raw, pickle, yaml.load, etc.
* presencia o ausencia de sanitización/escape/validación
* conteos de patrones sospechosos
* longitud del código
* cantidad de imports
* posibles patrones de inyección SQL, command injection, hardcoded secrets u otros

5. Guardado del modelo

* El modelo final entrenado debe guardarse en una ruta clara, por ejemplo:
  model/vulnerability_model.joblib
* Si se usa vectorizador, scaler o encoder, también deben guardarse:
  model/vectorizer.joblib
  model/scaler.joblib
  model/label_encoder.joblib
* El pipeline debe poder cargar estos archivos sin depender del notebook.

6. Crear/adaptar scripts para análisis del código modificado

* Crea o adapta scripts para que el pipeline pueda analizar el diff de un Pull Request.
* El script debe:
  * obtener los archivos modificados
  * leer solo código relevante
  * extraer features
  * cargar el modelo entrenado
  * clasificar como SEGURO o VULNERABLE
  * devolver probabilidad o score
  * generar un resultado en JSON
* Ejemplo de salida:
  {
  "status": "VULNERABLE",
  "probability": 0.91,
  "details": "...",
  "files": [...]
  }

7. Crear el pipeline CI/CD completo en el repositorio

* Crea o adapta un workflow de GitHub Actions en:
  .github/workflows/secure-pipeline.yml
* El flujo debe activarse automáticamente al crear o actualizar un Pull Request desde dev hacia test.
* El pipeline debe incluir estas fases:

Fase 1: Inicio de revisión de seguridad

* Enviar notificación Telegram indicando que inició el análisis.

Fase 2: Análisis con modelo ML

* Descargar el diff del PR.
* Ejecutar el script de análisis.
* Si el resultado es VULNERABLE:
  * bloquear el merge
  * fallar el job
  * comentar el PR con el detalle
  * crear una issue automática vinculada al PR
  * aplicar label “fixing-required”
  * enviar notificación Telegram
* Si el resultado es SEGURO:
  * comentar el PR indicando que pasó la revisión
  * enviar notificación Telegram
  * continuar el pipeline

Fase 3: Merge automático a test

* Si el análisis fue seguro, hacer merge automático hacia test.
* Notificar por Telegram.

Fase 4: Pruebas

* Ejecutar pruebas unitarias e integración según el proyecto:
  * pytest si es Python
  * npm test / Jest si es Node
  * JUnit si es Java
  * o adaptar según lo que exista
* Si fallan:
  * bloquear pipeline
  * aplicar label “tests-failed”
  * comentar el PR
  * notificar Telegram

Fase 5: Merge automático a main

* Solo si las pruebas pasan.
* Hacer merge automático hacia main.

Fase 6: Build y despliegue

* Crear build o imagen Docker según el proyecto.
* Adaptar el despliegue al proveedor gratuito que ya esté configurado o dejarlo preparado para Render, Railway, Fly.io, Vercel o Docker Hub.
* Notificar éxito o fallo por Telegram.

8. Telegram

* Implementa o adapta script para enviar mensajes Telegram.
* El token y chat_id deben leerse desde GitHub Secrets:
  TELEGRAM_BOT_TOKEN
  TELEGRAM_CHAT_ID
* No hardcodear secretos.
* Agrega mensajes para:
  * inicio de revisión de seguridad
  * resultado del modelo
  * rechazo por vulnerabilidad
  * merge a test
  * resultado de pruebas
  * merge a main
  * despliegue exitoso o fallido

9. GitHub Actions y permisos

* Configura el workflow con los permisos necesarios para:
  * leer código
  * comentar PRs
  * crear issues
  * aplicar labels
  * hacer merge
* Usa GITHUB_TOKEN cuando sea posible.
* Si se requiere PAT, documenta claramente el secret necesario.

10. Branch protection

* Agrega en el README instrucciones para configurar branch protection rules en test y main.
* Indica que el merge debe requerir que el workflow de seguridad pase correctamente.

11. README
    Actualiza o crea un README.md completo que explique:

* objetivo del proyecto
* estructura del repositorio
* cómo entrenar el modelo
* cómo ejecutar el notebook
* cómo ejecutar el análisis localmente
* cómo funciona el pipeline
* qué secrets deben configurarse
* cómo configurar Telegram
* cómo configurar branch protection
* cómo hacer una prueba con código vulnerable
* cómo hacer una prueba con código seguro
* cómo desplegar

12. Mantener compatibilidad y orden

* No rompas funcionalidades existentes.
* Si cambias rutas o nombres, actualiza todos los imports y referencias.
* Usa nombres claros.
* Agrega comentarios donde sea necesario.
* El código debe ser ejecutable tanto localmente como dentro de GitHub Actions.
* Evita dependencias innecesarias.
* Si agregas dependencias, actualiza requirements.txt, pyproject.toml, package.json o el archivo correspondiente.

13. Entregables esperados dentro del repositorio
    Al finalizar, el proyecto debe contener como mínimo:

* notebook de entrenamiento
* scripts de extracción de features
* scripts de análisis del PR/diff
* modelo guardado .joblib o .pkl
* workflow CI/CD seguro
* script de notificación Telegram
* README actualizado
* requirements actualizados
* ejemplos de código seguro y vulnerable para probar el flujo

Importante:
Antes de modificar, revisa el código existente y adapta lo que ya hay. No quiero una solución aislada que ignore el proyecto actual. Quiero que el repositorio quede funcionando con el flujo completo requerido.
