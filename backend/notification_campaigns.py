from __future__ import annotations

import json
import os
from datetime import datetime, timezone
from typing import Optional

import httpx
from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy import Boolean, DateTime, Integer, String, Text, create_engine, select
from sqlalchemy.orm import DeclarativeBase, Mapped, Session, mapped_column, sessionmaker

DATABASE_URL = os.getenv("DATABASE_URL", "sqlite:///./faleora.db")
PUSH_PROVIDER_URL = os.getenv("PUSH_PROVIDER_URL", "")
PUSH_API_KEY = os.getenv("PUSH_API_KEY", "")
NOTIFICATION_MODE = os.getenv("NOTIFICATION_MODE", "dry_run")
connect_args = {"check_same_thread": False} if DATABASE_URL.startswith("sqlite") else {}
engine = create_engine(DATABASE_URL, future=True, connect_args=connect_args)
SessionLocal = sessionmaker(bind=engine, autoflush=False, expire_on_commit=False)

class Base(DeclarativeBase):
    pass

class AudienceMember(Base):
    __tablename__ = "notification_audience_members"
    id: Mapped[int] = mapped_column(primary_key=True)
    member_type: Mapped[str] = mapped_column(String(30), index=True)  # user|venue|partner|staff
    name: Mapped[str] = mapped_column(String(160))
    email: Mapped[Optional[str]] = mapped_column(String(200), nullable=True)
    phone: Mapped[Optional[str]] = mapped_column(String(60), nullable=True)
    push_token: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    city: Mapped[Optional[str]] = mapped_column(String(120), nullable=True, index=True)
    plan: Mapped[Optional[str]] = mapped_column(String(40), nullable=True, index=True)
    tags: Mapped[str] = mapped_column(Text, default="")
    inactive_days: Mapped[int] = mapped_column(Integer, default=0)
    consent_email: Mapped[bool] = mapped_column(Boolean, default=False)
    consent_sms: Mapped[bool] = mapped_column(Boolean, default=False)
    consent_whatsapp: Mapped[bool] = mapped_column(Boolean, default=False)
    consent_push: Mapped[bool] = mapped_column(Boolean, default=False)
    license_status: Mapped[Optional[str]] = mapped_column(String(30), nullable=True)
    active: Mapped[bool] = mapped_column(Boolean, default=True)

class NotificationCampaign(Base):
    __tablename__ = "notification_campaigns"
    id: Mapped[int] = mapped_column(primary_key=True)
    title: Mapped[str] = mapped_column(String(180))
    message: Mapped[str] = mapped_column(Text)
    action_url: Mapped[Optional[str]] = mapped_column(String(400), nullable=True)
    audiences_json: Mapped[str] = mapped_column(Text)
    channels_json: Mapped[str] = mapped_column(Text)
    city_filter: Mapped[Optional[str]] = mapped_column(String(120), nullable=True)
    tag_filter: Mapped[Optional[str]] = mapped_column(String(120), nullable=True)
    priority: Mapped[str] = mapped_column(String(20), default="normal")
    scheduled_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True, index=True)
    status: Mapped[str] = mapped_column(String(30), default="draft", index=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))

class DeliveryLog(Base):
    __tablename__ = "notification_delivery_logs"
    id: Mapped[int] = mapped_column(primary_key=True)
    campaign_id: Mapped[int] = mapped_column(Integer, index=True)
    member_id: Mapped[int] = mapped_column(Integer, index=True)
    channel: Mapped[str] = mapped_column(String(30), index=True)
    recipient: Mapped[str] = mapped_column(String(255))
    status: Mapped[str] = mapped_column(String(30), index=True)
    provider: Mapped[str] = mapped_column(String(60), default="")
    error: Mapped[str] = mapped_column(Text, default="")
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))

Base.metadata.create_all(engine)
router = APIRouter(prefix="/api/notification-campaigns", tags=["notification-campaigns"])

class CampaignCreate(BaseModel):
    title: str
    message: str
    action_url: Optional[str] = None
    audiences: list[str]
    channels: list[str]
    city: Optional[str] = None
    tags: Optional[str] = None
    priority: str = "normal"
    scheduled_at: Optional[datetime] = None

class MemberCreate(BaseModel):
    member_type: str
    name: str
    email: Optional[str] = None
    phone: Optional[str] = None
    push_token: Optional[str] = None
    city: Optional[str] = None
    plan: Optional[str] = None
    tags: str = ""
    inactive_days: int = 0
    consent_email: bool = False
    consent_sms: bool = False
    consent_whatsapp: bool = False
    consent_push: bool = False
    license_status: Optional[str] = None

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

def _matches(member: AudienceMember, groups: list[str], city: Optional[str], tag: Optional[str]) -> bool:
    matched = False
    for g in groups:
        if g == "users_all" and member.member_type == "user": matched = True
        elif g == "users_free" and member.member_type == "user" and member.plan == "free": matched = True
        elif g == "users_plus" and member.member_type == "user" and member.plan == "plus": matched = True
        elif g == "users_premium" and member.member_type == "user" and member.plan == "premium": matched = True
        elif g == "users_black" and member.member_type == "user" and member.plan == "black": matched = True
        elif g == "users_inactive" and member.member_type == "user" and member.inactive_days >= 30: matched = True
        elif g == "users_city" and member.member_type == "user" and city and (member.city or "").lower() == city.lower(): matched = True
        elif g == "venues_all" and member.member_type == "venue": matched = True
        elif g == "venues_active" and member.member_type == "venue" and member.license_status in {"active", "trial"}: matched = True
        elif g == "venues_trial" and member.member_type == "venue" and member.license_status == "trial": matched = True
        elif g == "venues_expiring" and member.member_type == "venue" and member.license_status == "ending": matched = True
        elif g == "venues_expired" and member.member_type == "venue" and member.license_status == "expired": matched = True
        elif g == "venues_city" and member.member_type == "venue" and city and (member.city or "").lower() == city.lower(): matched = True
        elif g == "partners" and member.member_type == "partner": matched = True
        elif g == "staff" and member.member_type == "staff": matched = True
    if not matched:
        return False
    if tag and tag.lower() not in (member.tags or "").lower():
        return False
    return True

def _recipient(member: AudienceMember, channel: str) -> Optional[str]:
    if channel == "email" and member.consent_email: return member.email
    if channel == "sms" and member.consent_sms: return member.phone
    if channel == "whatsapp" and member.consent_whatsapp: return member.phone
    if channel == "push" and member.consent_push: return member.push_token
    return None

def _render(text: str, member: AudienceMember) -> str:
    return (text.replace("{name}", member.name)
                .replace("{venue}", member.name if member.member_type == "venue" else "")
                .replace("{city}", member.city or "")
                .replace("{plan}", member.plan or ""))

def _send_push(token: str, title: str, message: str, action_url: Optional[str]) -> tuple[str, str]:
    if NOTIFICATION_MODE == "dry_run":
        return "dry_run", "push-dry-run"
    if not PUSH_PROVIDER_URL:
        return "failed", "push-not-configured"
    response = httpx.post(PUSH_PROVIDER_URL, json={"token": token, "title": title, "message": message, "action_url": action_url}, headers={"Authorization": f"Bearer {PUSH_API_KEY}"} if PUSH_API_KEY else {}, timeout=20)
    response.raise_for_status()
    return "sent", "push-provider"

def dispatch_campaign(campaign_id: int, send_func=None) -> dict:
    db = SessionLocal()
    sent = failed = skipped = 0
    try:
        campaign = db.get(NotificationCampaign, campaign_id)
        if not campaign:
            return {"ok": False, "error": "campaign_not_found"}
        groups = json.loads(campaign.audiences_json)
        channels = json.loads(campaign.channels_json)
        members = db.scalars(select(AudienceMember).where(AudienceMember.active.is_(True))).all()
        for m in members:
            if not _matches(m, groups, campaign.city_filter, campaign.tag_filter):
                continue
            for channel in channels:
                recipient = _recipient(m, channel)
                if not recipient:
                    skipped += 1
                    continue
                existing = db.scalar(select(DeliveryLog.id).where(DeliveryLog.campaign_id == campaign.id, DeliveryLog.member_id == m.id, DeliveryLog.channel == channel))
                if existing:
                    skipped += 1
                    continue
                try:
                    message = _render(campaign.message, m)
                    title = _render(campaign.title, m)
                    if channel == "push":
                        status, provider = _send_push(recipient, title, message, campaign.action_url)
                    elif send_func:
                        status, provider = send_func(channel, recipient, message)
                    else:
                        status, provider = "dry_run", "no-provider"
                    if status in {"sent", "dry_run"}: sent += 1
                    else: failed += 1
                    error = ""
                except Exception as exc:
                    status, provider, error = "failed", "exception", str(exc)
                    failed += 1
                db.add(DeliveryLog(campaign_id=campaign.id, member_id=m.id, channel=channel, recipient=recipient, status=status, provider=provider, error=error))
        campaign.status = "sent" if failed == 0 else "partial"
        db.commit()
        return {"ok": True, "sent_or_dry_run": sent, "failed": failed, "skipped": skipped}
    finally:
        db.close()

def process_scheduled_campaigns(send_func=None) -> dict:
    db = SessionLocal()
    ids = []
    try:
        now = datetime.now(timezone.utc)
        rows = db.scalars(select(NotificationCampaign).where(NotificationCampaign.status == "scheduled", NotificationCampaign.scheduled_at <= now)).all()
        ids = [x.id for x in rows]
    finally:
        db.close()
    return {"processed": [dispatch_campaign(i, send_func) for i in ids]}

@router.post("/members")
def create_member(payload: MemberCreate, db: Session = Depends(get_db)):
    x = AudienceMember(**payload.model_dump())
    db.add(x); db.commit(); db.refresh(x)
    return {"id": x.id}

@router.post("")
def create_campaign(payload: CampaignCreate, db: Session = Depends(get_db)):
    if not payload.audiences or not payload.channels:
        raise HTTPException(400, "Hedef grup ve kanal zorunludur")
    x = NotificationCampaign(title=payload.title, message=payload.message, action_url=payload.action_url, audiences_json=json.dumps(payload.audiences), channels_json=json.dumps(payload.channels), city_filter=payload.city, tag_filter=payload.tags, priority=payload.priority, scheduled_at=payload.scheduled_at, status="scheduled" if payload.scheduled_at else "queued")
    db.add(x); db.commit(); db.refresh(x)
    return {"id": x.id, "status": x.status}

@router.post("/{campaign_id}/send")
def send_campaign(campaign_id: int):
    return dispatch_campaign(campaign_id)

@router.get("")
def list_campaigns(db: Session = Depends(get_db)):
    rows = db.scalars(select(NotificationCampaign).order_by(NotificationCampaign.created_at.desc()).limit(200)).all()
    return [{"id": x.id, "title": x.title, "status": x.status, "audiences": json.loads(x.audiences_json), "channels": json.loads(x.channels_json), "scheduled_at": x.scheduled_at, "created_at": x.created_at} for x in rows]

@router.get("/{campaign_id}/report")
def campaign_report(campaign_id: int, db: Session = Depends(get_db)):
    rows = db.scalars(select(DeliveryLog).where(DeliveryLog.campaign_id == campaign_id)).all()
    stats = {"sent": 0, "dry_run": 0, "failed": 0}
    by_channel = {}
    for r in rows:
        stats[r.status] = stats.get(r.status, 0) + 1
        by_channel.setdefault(r.channel, {"sent": 0, "dry_run": 0, "failed": 0})
        by_channel[r.channel][r.status] = by_channel[r.channel].get(r.status, 0) + 1
    return {"campaign_id": campaign_id, "total": len(rows), "stats": stats, "by_channel": by_channel}
