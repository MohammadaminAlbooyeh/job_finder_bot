import os
import requests
from typing import Dict, List


def send_telegram_message(bot_token: str, chat_id: str, text: str):
    if not bot_token or not chat_id or not text:
        raise ValueError("TELEGRAM_TOKEN, TELEGRAM_CHAT_ID and text are required")

    url = f"https://api.telegram.org/bot{bot_token}/sendMessage"
    resp = requests.post(url, json={"chat_id": chat_id, "text": text, "parse_mode": "HTML"}, timeout=15)
    resp.raise_for_status()


def notify_jobs_via_telegram(jobs: List[Dict]):
    token = os.getenv("TELEGRAM_TOKEN")
    chat_id = os.getenv("TELEGRAM_CHAT_ID")
    if not token or not chat_id:
        raise ValueError("TELEGRAM_TOKEN and TELEGRAM_CHAT_ID are required for Telegram notifications")

    if not jobs:
        return

    text_lines = [f"<b>Job Finder Bot</b> - {len(jobs)} new job(s):\n"]
    for job in jobs[:10]:
        line = f"<a href='{job.get('url')}'>{job.get('title')}</a> @ {job.get('company')} ({job.get('location')})"
        text_lines.append(line)

    if len(jobs) > 10:
        text_lines.append(f"... and {len(jobs)-10} more")

    send_telegram_message(bot_token=token, chat_id=chat_id, text="\n".join(text_lines))
