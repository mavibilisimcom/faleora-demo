from __future__ import annotations

from fastapi import APIRouter
from pydantic import BaseModel

from main import settings
from provider_dispatch import dispatch_notification

router = APIRouter(prefix="/api/providers", tags=["providers"])


class ProviderTest(BaseModel):
    channel: str
    recipient: str
    message: str = "FALEORA bildirim altyapısı test mesajı."
    title: str = "FALEORA Test Bildirimi"


def _configured(value: str) -> bool:
    return bool((value or "").strip())


@router.get("/status")
def provider_status():
    return {
        "notification_mode": settings.notification_mode,
        "email": {
            "configured": _configured(settings.smtp_host) and _configured(settings.smtp_from),
            "host": settings.smtp_host or None,
            "from": settings.smtp_from or None,
        },
        "sms": {
            "configured": _configured(settings.sms_provider_url) and _configured(settings.sms_api_key),
            "endpoint": settings.sms_provider_url or None,
        },
        "whatsapp": {
            "configured": _configured(settings.whatsapp_provider_url) and _configured(settings.whatsapp_api_key),
            "endpoint": settings.whatsapp_provider_url or None,
        },
        "push": {
            "configured": _configured(getattr(settings, "push_provider_url", "")) and _configured(getattr(settings, "push_api_key", "")),
            "endpoint": getattr(settings, "push_provider_url", "") or None,
        },
    }


@router.post("/test")
def test_provider(payload: ProviderTest):
    status, provider = dispatch_notification(payload.channel, payload.recipient, payload.message, payload.title)
    return {"status": status, "provider": provider, "channel": payload.channel, "recipient": payload.recipient}
