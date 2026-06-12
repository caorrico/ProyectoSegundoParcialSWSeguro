# Estado Actual y Tareas Faltantes
**Fecha:** 12 de Junio de 2026

## ✅ Lo que ya está terminado (y en el repositorio)

1. **Modelo de Minería de Datos (IA) sin LLMs**:
   - Random Forest entrenado usando TF-IDF (tokens) y AST (features sintácticas extraídas con `tree-sitter`).
   - Satisface el requisito estricto: *"Estricta prohibición de LLMs (GPT, Claude, etc). El modelo debe ser de ML tradicional"*.
   - Exactitud / Accuracy superior al 82% (85.87%).
   - Script para autogenerar un dataset del OWASP Top 10 2025 para entrenamiento.

2. **Backend API (FastAPI) preparado para Deploy**:
   - Creado `app/interfaces/api.py` para exponer el modelo vía HTTP.
   - Definidos endpoints `/health`, `/predict`, y `/scan`.
   - Creados archivos `Dockerfile` y `render.yaml` listos para Render o Railway.

3. **Notificaciones de Telegram preparadas**:
   - El script `.github/workflows/security-mining.yml` tiene incluidos los `curl` para notificar en todas las fases.
   - Creado el script `scripts/setup_telegram.py` para facilitar la obtención del `TELEGRAM_CHAT_ID`.

4. **Pipeline CI/CD en etapas (GitHub Actions)**:
   - Configurado en `security-mining.yml` para dispararse en el evento `pull_request` a la rama `test`.
   - Dividido en 3 etapas: `security-review` (evaluación), `run-tests` (pruebas y merge automático), y `deploy` (merge a `main` y deploy).
   - Bloqueos automáticos, creación de issues (`🐛 Crear Issue automática`) y etiquetas (`fixing-required`) configuradas.

---

## 🚨 LO QUE FALTA (POR HACER AHORA)

1. **Configurar el Bot de Telegram en GitHub Secrets**
   - Tienes que correr `python scripts/setup_telegram.py --token <TU_TOKEN>`
   - Copiar el Token y Chat ID y ponerlos en **GitHub Secrets**:
     - `TELEGRAM_BOT_TOKEN`
     - `TELEGRAM_CHAT_ID`

2. **Conectar Render / Railway al repositorio**
   - Tienes que crear un servicio web en Render.com conectado a este repositorio.
   - Extraer el **Deploy Hook URL** de Render y ponerlo en GitHub Secrets como `RENDER_DEPLOY_HOOK_URL`.
   - Poner la URL final de la aplicación en GitHub Secrets como `PRODUCTION_URL`.

3. **Crear la rama `test` remotamente**
   - Actualmente estás en `dev` y existe `main`. Falta crear la rama `test`.
   - Al crear un PR de `dev` a `test`, GitHub Actions se disparará por primera vez con el nuevo flujo.

4. **Reglas de Protección de Ramas (Branch Protection)**
   - En GitHub ir a Settings -> Branches.
   - Proteger `test` y `main` para requerir que el Job de Status Checks pase exitosamente.

5. **Documentación Final (Para el 18 de Junio)**
   - Completar el `README.md` con fotos del bot de Telegram.
   - Armar el notebook `.ipynb` con la validación de entrenamiento.
   - Armar el informe técnico en LaTeX (`.tex`).

---

**Resumen de la estrategia CI/CD instalada:**
El desarrollador codifica en `dev`. Hace un Pull Request a `test`.
El flujo de Actions evalúa. Si detecta fallas, **cierra / bloquea el PR, abre una Issue** y manda Telegram.
Si está libre de vulnerabilidades, Actions automáticamente hace merge a `test`, corre unit tests, y si todo sale bien, él mismo hace merge de `test` a `main` y dispara el deploy final en Render.
