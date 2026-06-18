#!/usr/bin/env python3
"""Configure the Telegram bot used by the CI/CD pipeline.

Usage:
    python scripts/setup_telegram.py --token YOUR_BOT_TOKEN
    python scripts/setup_telegram.py --token YOUR_BOT_TOKEN --chat-id YOUR_CHAT_ID

Then save TELEGRAM_BOT_TOKEN and TELEGRAM_CHAT_ID as GitHub Actions secrets.
"""

from __future__ import annotations

import argparse
import json
import sys
import urllib.request


def get_updates(token: str) -> dict:
    url = f"https://api.telegram.org/bot{token}/getUpdates"
    try:
        with urllib.request.urlopen(url, timeout=10) as response:
            return json.loads(response.read())
    except Exception as error:
        print(f"Error connecting to Telegram API: {error}", file=sys.stderr)
        sys.exit(1)


def get_bot_info(token: str) -> dict:
    url = f"https://api.telegram.org/bot{token}/getMe"
    try:
        with urllib.request.urlopen(url, timeout=10) as response:
            return json.loads(response.read())
    except Exception as error:
        print(f"Error verifying Telegram token: {error}", file=sys.stderr)
        sys.exit(1)


def send_test_message(token: str, chat_id: str) -> bool:
    url = f"https://api.telegram.org/bot{token}/sendMessage"
    data = json.dumps(
        {
            "chat_id": chat_id,
            "parse_mode": "HTML",
            "text": (
                "<b>SecureDataMining Bot configurado</b>\n\n"
                "La conexion con el pipeline CI/CD de DevSecOps esta activa.\n"
                "Recibiras notificaciones de analisis, bloqueo por vulnerabilidad, "
                "pruebas, merge y despliegue."
            ),
        }
    ).encode("utf-8")
    request = urllib.request.Request(url, data=data, headers={"Content-Type": "application/json"})
    try:
        with urllib.request.urlopen(request, timeout=10) as response:
            result = json.loads(response.read())
            return bool(result.get("ok"))
    except Exception as error:
        print(f"Error sending Telegram test message: {error}", file=sys.stderr)
        return False


def find_chat_id(token: str) -> str | None:
    updates = get_updates(token)
    if not updates.get("ok") or not updates.get("result"):
        return None
    message = updates["result"][-1].get("message") or updates["result"][-1].get("channel_post")
    if not message:
        return None
    return str(message["chat"]["id"])


def main() -> None:
    parser = argparse.ArgumentParser(description="Setup Telegram bot for the SecureDataMining pipeline")
    parser.add_argument("--token", required=True, help="Telegram bot token from BotFather")
    parser.add_argument("--chat-id", help="Target chat ID, if you already know it")
    args = parser.parse_args()

    print("SecureDataMining - Telegram setup")
    print("1. Verifying bot token...")
    bot_info = get_bot_info(args.token)
    if not bot_info.get("ok"):
        print("Invalid Telegram token.", file=sys.stderr)
        sys.exit(1)

    bot = bot_info["result"]
    print(f"   Bot verified: @{bot['username']} ({bot['first_name']})")

    chat_id = args.chat_id
    if not chat_id:
        print("\n2. Looking for chat ID...")
        print(f"   Send any message to @{bot['username']} in Telegram, then press ENTER here.")
        input()
        chat_id = find_chat_id(args.token)
        if not chat_id:
            print("No chat messages were found. Send a message to the bot and run this again.", file=sys.stderr)
            sys.exit(1)
        print(f"   Chat ID found: {chat_id}")

    print("\n3. Sending test message...")
    if not send_test_message(args.token, chat_id):
        print("Telegram test message failed.", file=sys.stderr)
        sys.exit(1)

    print("   Test message sent.")
    print("\nConfiguration completed. Save these GitHub Actions secrets:")
    print("  TELEGRAM_BOT_TOKEN = <your bot token>")
    print(f"  TELEGRAM_CHAT_ID = {chat_id}")


if __name__ == "__main__":
    main()
