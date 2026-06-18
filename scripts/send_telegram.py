from __future__ import annotations

import argparse
import json
import os
import sys
import urllib.parse
import urllib.request


def main() -> None:
    parser = argparse.ArgumentParser(description="Send a Telegram message using environment secrets.")
    parser.add_argument("--message", required=True, help="Message text")
    parser.add_argument("--parse-mode", default="HTML", help="Telegram parse mode")
    args = parser.parse_args()

    token = os.getenv("TELEGRAM_BOT_TOKEN")
    chat_id = os.getenv("TELEGRAM_CHAT_ID")
    if not token or not chat_id:
        print("Telegram secrets not configured; skipping notification.")
        return

    payload = urllib.parse.urlencode(
        {"chat_id": chat_id, "text": args.message, "parse_mode": args.parse_mode}
    ).encode("utf-8")
    request = urllib.request.Request(
        f"https://api.telegram.org/bot{token}/sendMessage",
        data=payload,
        method="POST",
    )
    try:
        with urllib.request.urlopen(request, timeout=15) as response:
            result = json.loads(response.read())
            if result.get("ok"):
                print("Telegram notification sent.")
            else:
                print(f"Telegram notification failed: {result}", file=sys.stderr)
    except Exception as error:
        print(f"Telegram notification failed: {error}", file=sys.stderr)


if __name__ == "__main__":
    main()
