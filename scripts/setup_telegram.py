#!/usr/bin/env python3
"""
Script de configuración del bot de Telegram.
Ejecutar UNA VEZ para obtener el CHAT_ID y verificar la conexión.

Uso:
    python scripts/setup_telegram.py --token YOUR_BOT_TOKEN
    
Luego copiar TELEGRAM_BOT_TOKEN y TELEGRAM_CHAT_ID a GitHub Secrets.
"""
import argparse
import urllib.request
import json
import sys


def get_updates(token: str) -> dict:
    url = f"https://api.telegram.org/bot{token}/getUpdates"
    try:
        with urllib.request.urlopen(url, timeout=10) as resp:
            return json.loads(resp.read())
    except Exception as e:
        print(f"Error conectando a Telegram API: {e}")
        sys.exit(1)


def get_bot_info(token: str) -> dict:
    url = f"https://api.telegram.org/bot{token}/getMe"
    with urllib.request.urlopen(url, timeout=10) as resp:
        return json.loads(resp.read())


def send_test_message(token: str, chat_id: str) -> bool:
    url = f"https://api.telegram.org/bot{token}/sendMessage"
    data = json.dumps({
        "chat_id": chat_id,
        "parse_mode": "HTML",
        "text": (
            "🤖 <b>SecureDataMining Bot configurado!</b>\n\n"
            "✅ La conexión con el pipeline CI/CD de DevSecOps está activa.\n"
            "Recibirás notificaciones en cada etapa del pipeline:\n\n"
            "🔍 Inicio de revisión de seguridad IA\n"
            "✅/❌ Resultado del modelo ML\n"
            "🔀 Merge a rama test\n"
            "🧪 Resultado de pruebas\n"
            "🚀 Deploy en producción\n"
            "🚨 Rechazo por vulnerabilidad\n\n"
            "<i>Universidad de las Fuerzas Armadas ESPE — Desarrollo de Software Seguro</i>"
        )
    }).encode()
    req = urllib.request.Request(url, data=data, headers={"Content-Type": "application/json"})
    try:
        with urllib.request.urlopen(req, timeout=10) as resp:
            result = json.loads(resp.read())
            return result.get("ok", False)
    except Exception as e:
        print(f"Error enviando mensaje: {e}")
        return False


def main():
    parser = argparse.ArgumentParser(description="Setup del bot de Telegram para el pipeline CI/CD")
    parser.add_argument("--token", required=True, help="Token del bot de Telegram (@BotFather)")
    parser.add_argument("--chat-id", help="Chat ID (si ya lo conoces)")
    args = parser.parse_args()

    token = args.token
    print(f"\n{'='*60}")
    print("SecureDataMining — Configuración de Bot Telegram")
    print(f"{'='*60}\n")

    # Verificar token
    print("1. Verificando token del bot...")
    bot_info = get_bot_info(token)
    if not bot_info.get("ok"):
        print(f"❌ Token inválido: {bot_info}")
        sys.exit(1)

    bot = bot_info["result"]
    print(f"   ✅ Bot: @{bot['username']} ({bot['first_name']})")

    chat_id = args.chat_id

    if not chat_id:
        print("\n2. Buscando chat ID...")
        print("   INSTRUCCIÓN: Envía cualquier mensaje al bot @{} en Telegram ahora.".format(bot['username']))
        print("   Luego presiona ENTER aquí...")
        input()

        updates = get_updates(token)
        if not updates.get("ok") or not updates.get("result"):
            print("   ❌ No se encontraron mensajes. Asegúrate de haber enviado un mensaje al bot.")
            sys.exit(1)

        chat_id = str(updates["result"][-1]["message"]["chat"]["id"])
        sender = updates["result"][-1]["message"]["from"].get("username", "unknown")
        print(f"   ✅ Chat ID encontrado: {chat_id} (de @{sender})")

    # Enviar mensaje de prueba
    print(f"\n3. Enviando mensaje de prueba al chat {chat_id}...")
    if send_test_message(token, chat_id):
        print("   ✅ Mensaje de prueba enviado exitosamente!")
    else:
        print("   ❌ Error enviando mensaje de prueba")
        sys.exit(1)

    # Mostrar instrucciones de GitHub Secrets
    print(f"\n{'='*60}")
    print("CONFIGURACIÓN COMPLETADA")
    print(f"{'='*60}")
    print("\nCopia estos valores en GitHub Secrets:")
    print(f"  Repositorio → Settings → Secrets → Actions → New secret\n")
    print(f"  Nombre: TELEGRAM_BOT_TOKEN")
    print(f"  Valor:  {token}\n")
    print(f"  Nombre: TELEGRAM_CHAT_ID")
    print(f"  Valor:  {chat_id}\n")
    print("Opcional (para deploy en Render):")
    print("  Nombre: RENDER_DEPLOY_HOOK_URL")
    print("  Valor:  (URL del deploy hook de Render.com)")
    print("\n  Nombre: PRODUCTION_URL")
    print("  Valor:  https://tu-app.onrender.com")
    print(f"\n{'='*60}\n")


if __name__ == "__main__":
    main()
