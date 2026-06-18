#!/usr/bin/env python3
"""
Bot de Telegram para SecureDataMining DevSecOps.
Permite enviar código fuente y obtener predicciones de vulnerabilidades directamente desde Telegram.
"""
import asyncio
import os
from pathlib import Path

# Fix for Windows asyncio event loop policy
if os.name == 'nt':
    asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())

from telegram import Update, Document
from telegram.ext import (
    Application,
    CommandHandler,
    MessageHandler,
    filters,
    ContextTypes,
)

from app.domain.entities import RawCodeModule
from app.domain.value_objects import RiskLevel
from app.shared.settings import settings
from app.infrastructure.ml.random_forest_predictor import RandomForestPredictor
from app.application.use_cases.predict_vulnerability import PredictVulnerabilityUseCase

HELP_TEXT = """
🤖 SecureDataMining DevSecOps Bot — Comandos disponibles:

/start - Saludo inicial
/help - Esta ayuda
/scan <código> - Analiza código fuente (C/C++/Java) para vulnerabilidades
También puedes enviar un archivo de código fuente (.c, .cpp, .java, .py, etc.)

Niveles de riesgo:
🟢 LOW (<40%)
🟡 MEDIUM (40-70%)
🔴 HIGH (≥70%)

Proyecto ESPE — Desarrollo de Software Seguro
"""


def build_predict_use_case() -> PredictVulnerabilityUseCase:
    predictor = RandomForestPredictor(settings.model_path)
    return PredictVulnerabilityUseCase(predictor)


async def start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    await update.message.reply_text(
        "¡Hola! 👋 Soy el bot de SecureDataMining DevSecOps.\n"
        "Puedes enviar código fuente para analizar vulnerabilidades.\n"
        "Usa /help para ver la lista de comandos."
    )


async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    await update.message.reply_text(HELP_TEXT)


async def scan_code(code: str, filename: str = "snippet.c") -> str:
    try:
        use_case = build_predict_use_case()
        metrics = RawCodeModule(raw_code=code)
        prediction = use_case.execute(metrics)

        risk_icon = {
            RiskLevel.HIGH: "🔴",
            RiskLevel.MEDIUM: "🟡",
            RiskLevel.LOW: "🟢",
        }.get(prediction.risk_level, "⚪")

        result_text = f"""
📊 Resultado del análisis para {filename}:

{risk_icon} Nivel de riesgo: {prediction.risk_level.value}
📈 Probabilidad: {prediction.risk_probability * 100:.1f}%
📜 Tipo de vulnerabilidad: {', '.join(prediction.vulnerability_types) if prediction.vulnerability_types else 'N/A'}
🏷️ CWE IDs: {', '.join(prediction.cwe_ids) if prediction.cwe_ids else 'N/A'}
💡 Recomendación: {prediction.recommendation}
"""
        return result_text
    except FileNotFoundError:
        return "❌ El modelo no está entrenado. Por favor, entrena el modelo primero con: python -m app.interfaces.cli train --use-owasp"
    except Exception as e:
        return f"❌ Error al analizar el código: {str(e)}"


async def handle_scan(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    if not context.args:
        await update.message.reply_text("⚠️ Por favor, proporciona código fuente después del comando /scan.\nEjemplo: /scan #include <stdio.h> int main() { ... }")
        return

    code = " ".join(context.args)
    result = await scan_code(code)
    await update.message.reply_text(result)


async def handle_document(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    document: Document = update.message.document
    file = await context.bot.get_file(document.file_id)

    # Download the file
    file_path = Path("temp_download") / document.file_name
    file_path.parent.mkdir(exist_ok=True)
    await file.download_to_drive(file_path)

    # Read the file
    code = file_path.read_text(encoding="utf-8", errors="replace")
    result = await scan_code(code, document.file_name)

    # Delete temp file
    file_path.unlink(missing_ok=True)

    await update.message.reply_text(result)


async def handle_text(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    if not update.message.text.startswith("/"):
        result = await scan_code(update.message.text)
        await update.message.reply_text(result)


def main() -> None:
    token = os.getenv("TELEGRAM_BOT_TOKEN")
    if not token:
        raise RuntimeError("TELEGRAM_BOT_TOKEN is required to start the Telegram bot.")

    application = Application.builder().token(token).build()

    application.add_handler(CommandHandler("start", start))
    application.add_handler(CommandHandler("help", help_command))
    application.add_handler(CommandHandler("scan", handle_scan))
    application.add_handler(MessageHandler(filters.Document.ALL, handle_document))
    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_text))

    print("SecureDataMining Telegram Bot iniciado...")
    
    # Set up event loop for Python 3.14 compatibility
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    try:
        application.run_polling()
    finally:
        loop.close()


if __name__ == "__main__":
    main()
