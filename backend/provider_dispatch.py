from __future__ import annotations

import os
import smtplib
from email.message import EmailMessage

import httpx

from main import settings


def _post(url: str, api_key: str, payload: dict) -> tuple[str, str]:
    if not url:
        return "failed", "provider_not_configured"
    headers = {"Content-Type": "application/json"}
    if api_key:
        headers["Authorization"] = f"Bearer {api_key}"
    response = httpx.post(url, json=payload, headers=headers, timeout=20)
    response.raise_for_status()
    return "sent", "http_api"


def dispatch_notification(channel: str, recipient: str, message: str, title: str = "FALEORA Bildirimi") -> tuple[str, str]:
    if settings.notification_mode == "dry_run":
        return "dry_run", "not_sent"

    c = channel.lower().strip()

    if c in {"email", "e-posta", "mail"} or "mail" in c:
        if not settings.smtp_host or not settings.smtp_from:
            return "failed", "smtp_not_configured"
        msg = EmailMessage()
        msg["Subject"] = title
        msg["From"] = settings.smtp_from
        msg["To"] = recipient
        msg.set_content(message)
        with smtplib.SMTP(settings.smtp_host, settings.smtp_port, timeout=20) as smtp:
            smtp.starttls()
            if settings.smtp_user:
                smtp.login(settings.smtp_user, settings.smtp_password)
            smtp.send_message(msg)
        return "sent", "smtp"

    if "whatsapp" in c:
        return _post(settings.whatsapp_provider_url, settings.whatsapp_api_key, {"to": recipient, "message": message})

    if "sms" in c:
        return _post(settings.sms_provider_url, settings.sms_api_key, {"to": recipient, "message": message})

    if "push" in c:
        push_url = os.getenv("PUSH_PROVIDER_URL", "")
        push_key = os.getenv("PUSH_API_KEY", "")
        return _post(push_url, push_key, {"to": recipient, "title": title, "message": message})

    return "failed", "unknown_channel"
