from __future__ import annotations

import hashlib
import hmac
import json
import os
import smtplib
from datetime import date, datetime, timedelta, timezone
from email.message import EmailMessage
from enum import Enum
from typing import Optional

import httpx
from apscheduler.schedulers.background import BackgroundScheduler
from fastapi import Depends, FastAPI, Header, HTTPException, Request
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, EmailStr
from pydantic_settings import BaseSettings, SettingsConfigDict
from sqlalchemy import Boolean, Date, DateTime, ForeignKey, Integer, String, Text, create_engine, select
from sqlalchemy.orm import DeclarativeBase, Mapped, Session, mapped_column, relationship, sessionmaker


class Settings(BaseSettings):
    app_env: str = "development"
    database_url: str = "sqlite:///./faleora.db"
    frontend_origins: str = "https://mavibilisimcom.github.io"
    timezone: str = "Europe/Istanbul"
    reminder_hour: int = 9
    notification_mode: str = "dry_run"
    smtp_host: str = ""
    smtp_port: int = 587
    smtp_user: str = ""
    smtp_password: str = ""
    smtp_from: str = ""
    sms_provider_url: str = ""
    sms_api_key: str = ""
    whatsapp_provider_url: str = ""
    whatsapp_api_key: str = ""
    payment_provider: str = "manual"
    payment_webhook_secret: str = ""
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")


settings = Settings()


class Base(DeclarativeBase):
    pass


class Venue(Base):
    __tablename__ = "venues"
    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(String(160), index=True)
    contact_email: Mapped[Optional[str]] = mapped_column(String(200), nullable=True)
    contact_phone: Mapped[Optional[str]] = mapped_column(String(60), nullable=True)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))
    licenses: Mapped[list["License"]] = relationship(back_populates="venue", cascade="all, delete-orphan")


class License(Base):
    __tablename__ = "licenses"
    id: Mapped[int] = mapped_column(primary_key=True)
    venue_id: Mapped[int] = mapped_column(ForeignKey("venues.id"), index=True)
    plan_code: Mapped[str] = mapped_column(String(40))
    starts_at: Mapped[date] = mapped_column(Date)
    expires_at: Mapped[date] = mapped_column(Date, index=True)
    renewal_mode: Mapped[str] = mapped_column(String(20), default="manual")
    status: Mapped[str] = mapped_column(String(20), default="active", index=True)
    grace_days: Mapped[int] = mapped_column(Integer, default=0)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))
    venue: Mapped[Venue] = relationship(back_populates="licenses")


class ReminderRule(Base):
    __tablename__ = "reminder_rules"
    id: Mapped[int] = mapped_column(primary_key=True)
    days_before: Mapped[int] = mapped_column(Integer, index=True)
    channel: Mapped[str] = mapped_column(String(30))
    template: Mapped[str] = mapped_column(Text)
    enabled: Mapped[bool] = mapped_column(Boolean, default=True)


class NotificationLog(Base):
    __tablename__ = "notification_logs"
    id: Mapped[int] = mapped_column(primary_key=True)
    license_id: Mapped[int] = mapped_column(ForeignKey("licenses.id"), index=True)
    channel: Mapped[str] = mapped_column(String(30))
    recipient: Mapped[str] = mapped_column(String(220))
    status: Mapped[str] = mapped_column(String(30))
    payload: Mapped[str] = mapped_column(Text)
    sent_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))


class Payment(Base):
    __tablename__ = "payments"
    id: Mapped[int] = mapped_column(primary_key=True)
    license_id: Mapped[int] = mapped_column(ForeignKey("licenses.id"), index=True)
    provider: Mapped[str] = mapped_column(String(40))
    provider_ref: Mapped[Optional[str]] = mapped_column(String(120), nullable=True)
    amount_minor: Mapped[int] = mapped_column(Integer, default=0)
    currency: Mapped[str] = mapped_column(String(8), default="TRY")
    status: Mapped[str] = mapped_column(String(30), default="pending")
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))


connect_args = {"check_same_thread": False} if settings.database_url.startswith("sqlite") else {}
engine = create_engine(settings.database_url, future=True, connect_args=connect_args)
SessionLocal = sessionmaker(bind=engine, autoflush=False, expire_on_commit=False)
Base.metadata.create_all(engine)


PLAN_DAYS = {"trial_7d": 7, "business_6m": 183, "business_1y": 365, "business_2y": 730}
DEFAULT_TEMPLATE = "FALEORA Business aboneliğiniz {days} gün sonra sona erecek. Hizmet kesintisi yaşamamak için yenileme işleminizi tamamlayabilirsiniz."


class LicenseStatus(str, Enum):
    trial = "trial"
    active = "active"
    grace = "grace"
    expired = "expired"
    suspended = "suspended"


class VenueCreate(BaseModel):
    name: str
    contact_email: Optional[EmailStr] = None
    contact_phone: Optional[str] = None


class LicenseCreate(BaseModel):
    venue_id: int
    plan_code: str
    starts_at: date = date.today()
    renewal_mode: str = "manual"


class ExtendLicense(BaseModel):
    days: int


class ReminderRuleCreate(BaseModel):
    days_before: int
    channel: str
    template: str = DEFAULT_TEMPLATE
    enabled: bool = True


class PaymentCreate(BaseModel):
    license_id: int
    amount_minor: int
    currency: str = "TRY"


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def days_left(lic: License) -> int:
    return (lic.expires_at - date.today()).days


def normalize_status(lic: License) -> str:
    if lic.status == LicenseStatus.suspended.value:
        return lic.status
    d = days_left(lic)
    if d < 0:
        if lic.grace_days and d >= -lic.grace_days:
            return LicenseStatus.grace.value
        return LicenseStatus.expired.value
    if lic.plan_code == "trial_7d":
        return LicenseStatus.trial.value
    return LicenseStatus.active.value


def resolve_recipient(v: Venue, channel: str) -> Optional[str]:
    c = channel.lower()
    if "mail" in c or "e-posta" in c:
        return v.contact_email
    if "sms" in c or "whatsapp" in c:
        return v.contact_phone
    return v.contact_email or v.contact_phone


def send_notification(channel: str, recipient: str, message: str) -> tuple[str, str]:
    if settings.notification_mode == "dry_run":
        return "dry_run", "not_sent"

    c = channel.lower()
    if "mail" in c or "e-posta" in c:
        if not all([settings.smtp_host, settings.smtp_from]):
            return "failed", "smtp_not_configured"
        msg = EmailMessage()
        msg["Subject"] = "FALEORA Business abonelik yenileme hatırlatması"
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
        if not settings.whatsapp_provider_url:
            return "failed", "whatsapp_not_configured"
        r = httpx.post(settings.whatsapp_provider_url, json={"to": recipient, "message": message}, headers={"Authorization": f"Bearer {settings.whatsapp_api_key}"}, timeout=20)
        r.raise_for_status()
        return "sent", "whatsapp"

    if "sms" in c:
        if not settings.sms_provider_url:
            return "failed", "sms_not_configured"
        r = httpx.post(settings.sms_provider_url, json={"to": recipient, "message": message}, headers={"Authorization": f"Bearer {settings.sms_api_key}"}, timeout=20)
        r.raise_for_status()
        return "sent", "sms"

    return "failed", "unknown_channel"


def process_due_reminders() -> dict:
    db = SessionLocal()
    sent = skipped = failed = 0
    try:
        rules = db.scalars(select(ReminderRule).where(ReminderRule.enabled.is_(True))).all()
        licenses = db.scalars(select(License)).all()
        for lic in licenses:
            lic.status = normalize_status(lic)
            if lic.status in {LicenseStatus.suspended.value, LicenseStatus.expired.value}:
                continue
            d = days_left(lic)
            for rule in rules:
                if d != rule.days_before:
                    continue
                already = db.scalar(select(NotificationLog).where(NotificationLog.license_id == lic.id, NotificationLog.channel == rule.channel, NotificationLog.payload.like(f'%"days": {d}%')))
                if already:
                    skipped += 1
                    continue
                recipient = resolve_recipient(lic.venue, rule.channel)
                if not recipient:
                    skipped += 1
                    continue
                message = rule.template.format(days=d, venue=lic.venue.name, expires_at=lic.expires_at.isoformat())
                try:
                    status, provider = send_notification(rule.channel, recipient, message)
                    if status in {"sent", "dry_run"}:
                        sent += 1
                    else:
                        failed += 1
                except Exception as exc:
                    status, provider, message = "failed", "exception", f"{message} | {exc}"
                    failed += 1
                db.add(NotificationLog(license_id=lic.id, channel=rule.channel, recipient=recipient, status=status, payload=json.dumps({"days": d, "provider": provider, "message": message}, ensure_ascii=False)))
        db.commit()
        return {"processed": True, "sent_or_dry_run": sent, "skipped": skipped, "failed": failed}
    finally:
        db.close()


app = FastAPI(title="FALEORA Business API", version="1.0.0")
app.add_middleware(CORSMiddleware, allow_origins=[x.strip() for x in settings.frontend_origins.split(",") if x.strip()], allow_credentials=True, allow_methods=["*"], allow_headers=["*"])

scheduler = BackgroundScheduler(timezone=settings.timezone)
scheduler.add_job(process_due_reminders, "cron", hour=settings.reminder_hour, minute=0, id="license_reminders", replace_existing=True)
scheduler.start()


@app.get("/health")
def health():
    return {"ok": True, "env": settings.app_env, "notification_mode": settings.notification_mode, "payment_provider": settings.payment_provider}


@app.post("/api/venues")
def create_venue(payload: VenueCreate, db: Session = Depends(get_db)):
    v = Venue(name=payload.name, contact_email=str(payload.contact_email) if payload.contact_email else None, contact_phone=payload.contact_phone)
    db.add(v); db.commit(); db.refresh(v)
    return {"id": v.id, "name": v.name}


@app.get("/api/licenses")
def list_licenses(db: Session = Depends(get_db)):
    rows = db.scalars(select(License).order_by(License.expires_at.asc())).all()
    out = []
    for lic in rows:
        lic.status = normalize_status(lic)
        out.append({"id": lic.id, "venue_id": lic.venue_id, "venue": lic.venue.name, "plan_code": lic.plan_code, "starts_at": lic.starts_at, "expires_at": lic.expires_at, "renewal_mode": lic.renewal_mode, "status": lic.status, "days_left": days_left(lic), "contact_email": lic.venue.contact_email, "contact_phone": lic.venue.contact_phone})
    db.commit()
    return out


@app.post("/api/licenses")
def create_license(payload: LicenseCreate, db: Session = Depends(get_db)):
    if payload.plan_code not in PLAN_DAYS:
        raise HTTPException(400, "Geçersiz plan")
    venue = db.get(Venue, payload.venue_id)
    if not venue:
        raise HTTPException(404, "Mekân bulunamadı")
    days = PLAN_DAYS[payload.plan_code]
    lic = License(venue_id=venue.id, plan_code=payload.plan_code, starts_at=payload.starts_at, expires_at=payload.starts_at + timedelta(days=days), renewal_mode=payload.renewal_mode, status="trial" if payload.plan_code == "trial_7d" else "active")
    db.add(lic); db.commit(); db.refresh(lic)
    return {"id": lic.id, "expires_at": lic.expires_at, "status": lic.status}


@app.post("/api/licenses/{license_id}/extend")
def extend_license(license_id: int, payload: ExtendLicense, db: Session = Depends(get_db)):
    lic = db.get(License, license_id)
    if not lic:
        raise HTTPException(404, "Lisans bulunamadı")
    base = max(lic.expires_at, date.today())
    lic.expires_at = base + timedelta(days=payload.days)
    lic.status = LicenseStatus.active.value
    db.commit()
    return {"id": lic.id, "expires_at": lic.expires_at, "status": lic.status}


@app.post("/api/licenses/{license_id}/suspend")
def suspend_license(license_id: int, db: Session = Depends(get_db)):
    lic = db.get(License, license_id)
    if not lic:
        raise HTTPException(404, "Lisans bulunamadı")
    lic.status = LicenseStatus.suspended.value if lic.status != LicenseStatus.suspended.value else LicenseStatus.active.value
    db.commit()
    return {"id": lic.id, "status": lic.status}


@app.post("/api/reminder-rules")
def create_rule(payload: ReminderRuleCreate, db: Session = Depends(get_db)):
    if payload.days_before < 0 or payload.days_before > 365:
        raise HTTPException(400, "Geçersiz gün")
    rule = ReminderRule(days_before=payload.days_before, channel=payload.channel, template=payload.template, enabled=payload.enabled)
    db.add(rule); db.commit(); db.refresh(rule)
    return {"id": rule.id}


@app.post("/api/jobs/license-reminders")
def run_reminders():
    return process_due_reminders()


@app.get("/api/notifications")
def notification_logs(db: Session = Depends(get_db)):
    rows = db.scalars(select(NotificationLog).order_by(NotificationLog.sent_at.desc()).limit(200)).all()
    return [{"id": r.id, "license_id": r.license_id, "channel": r.channel, "recipient": r.recipient, "status": r.status, "sent_at": r.sent_at, "payload": json.loads(r.payload)} for r in rows]


@app.post("/api/payments")
def create_payment(payload: PaymentCreate, db: Session = Depends(get_db)):
    lic = db.get(License, payload.license_id)
    if not lic:
        raise HTTPException(404, "Lisans bulunamadı")
    p = Payment(license_id=lic.id, provider=settings.payment_provider, amount_minor=payload.amount_minor, currency=payload.currency, status="pending")
    db.add(p); db.commit(); db.refresh(p)
    if settings.payment_provider == "manual":
        return {"payment_id": p.id, "status": "pending", "mode": "manual", "message": "Ödeme sağlayıcısı bağlanana kadar manuel tahsilat kaydıdır."}
    return {"payment_id": p.id, "status": p.status, "provider": p.provider}


@app.post("/api/payments/webhook")
async def payment_webhook(request: Request, x_faleora_signature: Optional[str] = Header(None), db: Session = Depends(get_db)):
    raw = await request.body()
    if settings.payment_webhook_secret:
        expected = hmac.new(settings.payment_webhook_secret.encode(), raw, hashlib.sha256).hexdigest()
        if not x_faleora_signature or not hmac.compare_digest(expected, x_faleora_signature):
            raise HTTPException(401, "Geçersiz webhook imzası")
    data = json.loads(raw or b"{}")
    payment_id = int(data.get("payment_id", 0))
    status = str(data.get("status", ""))
    p = db.get(Payment, payment_id)
    if not p:
        raise HTTPException(404, "Ödeme bulunamadı")
    p.status = status or p.status
    p.provider_ref = data.get("provider_ref") or p.provider_ref
    if p.status == "paid":
        lic = db.get(License, p.license_id)
        if lic:
            lic.status = LicenseStatus.active.value
    db.commit()
    return {"ok": True}


@app.on_event("shutdown")
def shutdown_event():
    scheduler.shutdown(wait=False)
