from __future__ import annotations

import json
import os
from datetime import date, datetime, timezone
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, EmailStr
from sqlalchemy import Boolean, Date, DateTime, Integer, String, Text, create_engine, select
from sqlalchemy.orm import DeclarativeBase, Mapped, Session, mapped_column, sessionmaker

DATABASE_URL = os.getenv("DATABASE_URL", "sqlite:///./faleora.db")
connect_args = {"check_same_thread": False} if DATABASE_URL.startswith("sqlite") else {}
engine = create_engine(DATABASE_URL, future=True, connect_args=connect_args)
SessionLocal = sessionmaker(bind=engine, autoflush=False, expire_on_commit=False)


class Base(DeclarativeBase):
    pass


class OccasionRecipient(Base):
    __tablename__ = "occasion_recipients"
    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(String(160), index=True)
    audience_type: Mapped[str] = mapped_column(String(30), default="venue")
    venue_name: Mapped[Optional[str]] = mapped_column(String(160), nullable=True)
    email: Mapped[Optional[str]] = mapped_column(String(200), nullable=True)
    phone: Mapped[Optional[str]] = mapped_column(String(60), nullable=True)
    birthday: Mapped[Optional[date]] = mapped_column(Date, nullable=True, index=True)
    consent_email: Mapped[bool] = mapped_column(Boolean, default=True)
    consent_sms: Mapped[bool] = mapped_column(Boolean, default=False)
    consent_whatsapp: Mapped[bool] = mapped_column(Boolean, default=False)
    consent_push: Mapped[bool] = mapped_column(Boolean, default=False)
    active: Mapped[bool] = mapped_column(Boolean, default=True)


class Occasion(Base):
    __tablename__ = "occasions"
    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(String(160), index=True)
    occasion_type: Mapped[str] = mapped_column(String(30), index=True)  # birthday|religious|official|custom
    event_date: Mapped[Optional[date]] = mapped_column(Date, nullable=True, index=True)
    month: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    day: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    recurring_yearly: Mapped[bool] = mapped_column(Boolean, default=False)
    enabled: Mapped[bool] = mapped_column(Boolean, default=True)
    default_message: Mapped[str] = mapped_column(Text)


class OccasionRule(Base):
    __tablename__ = "occasion_rules"
    id: Mapped[int] = mapped_column(primary_key=True)
    occasion_type: Mapped[str] = mapped_column(String(30), index=True)
    days_before: Mapped[int] = mapped_column(Integer, default=0)
    channel: Mapped[str] = mapped_column(String(30), default="E-posta")
    target_audience: Mapped[str] = mapped_column(String(30), default="all")
    message_template: Mapped[str] = mapped_column(Text)
    enabled: Mapped[bool] = mapped_column(Boolean, default=True)


class OccasionLog(Base):
    __tablename__ = "occasion_logs"
    id: Mapped[int] = mapped_column(primary_key=True)
    occasion_key: Mapped[str] = mapped_column(String(180), index=True)
    recipient_id: Mapped[int] = mapped_column(Integer, index=True)
    channel: Mapped[str] = mapped_column(String(30))
    recipient: Mapped[str] = mapped_column(String(220))
    status: Mapped[str] = mapped_column(String(30))
    payload: Mapped[str] = mapped_column(Text)
    sent_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))


Base.metadata.create_all(engine)
router = APIRouter(prefix="/api/occasions", tags=["occasions"])

OFFICIAL_HOLIDAYS = [
    ("Yılbaşı", 1, 1, "Yeni yılınızı kutlar, sağlık, mutluluk ve başarı dileriz. ✨"),
    ("23 Nisan Ulusal Egemenlik ve Çocuk Bayramı", 4, 23, "23 Nisan Ulusal Egemenlik ve Çocuk Bayramımız kutlu olsun. 🇹🇷"),
    ("Emek ve Dayanışma Günü", 5, 1, "1 Mayıs Emek ve Dayanışma Günü kutlu olsun."),
    ("19 Mayıs Atatürk'ü Anma, Gençlik ve Spor Bayramı", 5, 19, "19 Mayıs Atatürk'ü Anma, Gençlik ve Spor Bayramımız kutlu olsun. 🇹🇷"),
    ("15 Temmuz Demokrasi ve Millî Birlik Günü", 7, 15, "15 Temmuz Demokrasi ve Millî Birlik Günü'nü saygıyla anıyoruz."),
    ("30 Ağustos Zafer Bayramı", 8, 30, "30 Ağustos Zafer Bayramımız kutlu olsun. 🇹🇷"),
    ("29 Ekim Cumhuriyet Bayramı", 10, 29, "29 Ekim Cumhuriyet Bayramımız kutlu olsun. 🇹🇷"),
]


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def seed_official_holidays(db: Session):
    count = db.scalar(select(Occasion.id).limit(1))
    if count:
        return
    for name, month, day, msg in OFFICIAL_HOLIDAYS:
        db.add(Occasion(name=name, occasion_type="official", month=month, day=day, recurring_yearly=True, default_message=msg))
    db.add(Occasion(name="Ramazan Bayramı", occasion_type="religious", recurring_yearly=False, default_message="Ramazan Bayramınızı kutlar; sağlık, huzur ve mutluluk dileriz. 🌙"))
    db.add(Occasion(name="Kurban Bayramı", occasion_type="religious", recurring_yearly=False, default_message="Kurban Bayramınızı kutlar; sevdiklerinizle birlikte sağlık ve huzur dileriz. 🌙"))
    db.commit()


class RecipientCreate(BaseModel):
    name: str
    audience_type: str = "venue"
    venue_name: Optional[str] = None
    email: Optional[EmailStr] = None
    phone: Optional[str] = None
    birthday: Optional[date] = None
    consent_email: bool = True
    consent_sms: bool = False
    consent_whatsapp: bool = False
    consent_push: bool = False


class OccasionCreate(BaseModel):
    name: str
    occasion_type: str
    event_date: Optional[date] = None
    month: Optional[int] = None
    day: Optional[int] = None
    recurring_yearly: bool = False
    default_message: str


class RuleCreate(BaseModel):
    occasion_type: str
    days_before: int = 0
    channel: str = "E-posta"
    target_audience: str = "all"
    message_template: str
    enabled: bool = True


def target_date_for(occ: Occasion, today: date) -> Optional[date]:
    if occ.recurring_yearly and occ.month and occ.day:
        candidate = date(today.year, occ.month, occ.day)
        if candidate < today:
            candidate = date(today.year + 1, occ.month, occ.day)
        return candidate
    return occ.event_date


def recipient_channel_address(r: OccasionRecipient, channel: str) -> Optional[str]:
    c = channel.lower()
    if "mail" in c or "e-posta" in c:
        return r.email if r.consent_email else None
    if "whatsapp" in c:
        return r.phone if r.consent_whatsapp else None
    if "sms" in c:
        return r.phone if r.consent_sms else None
    if "push" in c:
        return f"push:{r.id}" if r.consent_push else None
    return None


def render_message(template: str, recipient: OccasionRecipient, occasion_name: str) -> str:
    return template.format(name=recipient.name, venue=recipient.venue_name or "", occasion=occasion_name)


def process_due_occasions(send_func=None) -> dict:
    db = SessionLocal()
    sent = skipped = 0
    try:
        seed_official_holidays(db)
        today = date.today()
        recipients = db.scalars(select(OccasionRecipient).where(OccasionRecipient.active.is_(True))).all()
        rules = db.scalars(select(OccasionRule).where(OccasionRule.enabled.is_(True))).all()
        occasions = db.scalars(select(Occasion).where(Occasion.enabled.is_(True))).all()

        # Birthdays are generated per recipient.
        for r in recipients:
            if not r.birthday:
                continue
            birthday_this_year = date(today.year, r.birthday.month, r.birthday.day)
            if birthday_this_year < today:
                birthday_this_year = date(today.year + 1, r.birthday.month, r.birthday.day)
            for rule in [x for x in rules if x.occasion_type == "birthday"]:
                if (birthday_this_year - today).days != rule.days_before:
                    continue
                address = recipient_channel_address(r, rule.channel)
                if not address:
                    skipped += 1; continue
                key = f"birthday:{r.id}:{birthday_this_year.isoformat()}:{rule.days_before}:{rule.channel}"
                if db.scalar(select(OccasionLog.id).where(OccasionLog.occasion_key == key)):
                    skipped += 1; continue
                msg = render_message(rule.message_template, r, "Doğum Günü")
                status = "dry_run"
                if send_func:
                    status, _provider = send_func(rule.channel, address, msg)
                db.add(OccasionLog(occasion_key=key, recipient_id=r.id, channel=rule.channel, recipient=address, status=status, payload=json.dumps({"message": msg, "type": "birthday"}, ensure_ascii=False)))
                sent += 1

        for occ in occasions:
            target = target_date_for(occ, today)
            if not target:
                continue
            for rule in [x for x in rules if x.occasion_type == occ.occasion_type]:
                if (target - today).days != rule.days_before:
                    continue
                for r in recipients:
                    if rule.target_audience != "all" and r.audience_type != rule.target_audience:
                        continue
                    address = recipient_channel_address(r, rule.channel)
                    if not address:
                        skipped += 1; continue
                    key = f"occasion:{occ.id}:{target.isoformat()}:{r.id}:{rule.days_before}:{rule.channel}"
                    if db.scalar(select(OccasionLog.id).where(OccasionLog.occasion_key == key)):
                        skipped += 1; continue
                    msg = render_message(rule.message_template or occ.default_message, r, occ.name)
                    status = "dry_run"
                    if send_func:
                        status, _provider = send_func(rule.channel, address, msg)
                    db.add(OccasionLog(occasion_key=key, recipient_id=r.id, channel=rule.channel, recipient=address, status=status, payload=json.dumps({"message": msg, "occasion": occ.name}, ensure_ascii=False)))
                    sent += 1
        db.commit()
        return {"processed": True, "sent_or_dry_run": sent, "skipped": skipped}
    finally:
        db.close()


@router.get("")
def list_occasions(db: Session = Depends(get_db)):
    seed_official_holidays(db)
    rows = db.scalars(select(Occasion).order_by(Occasion.occasion_type, Occasion.name)).all()
    return [{"id": x.id, "name": x.name, "occasion_type": x.occasion_type, "event_date": x.event_date, "month": x.month, "day": x.day, "recurring_yearly": x.recurring_yearly, "enabled": x.enabled, "default_message": x.default_message} for x in rows]


@router.post("")
def create_occasion(payload: OccasionCreate, db: Session = Depends(get_db)):
    x = Occasion(**payload.model_dump())
    db.add(x); db.commit(); db.refresh(x)
    return {"id": x.id}


@router.post("/recipients")
def create_recipient(payload: RecipientCreate, db: Session = Depends(get_db)):
    r = OccasionRecipient(**payload.model_dump())
    db.add(r); db.commit(); db.refresh(r)
    return {"id": r.id}


@router.get("/recipients")
def list_recipients(db: Session = Depends(get_db)):
    rows = db.scalars(select(OccasionRecipient).order_by(OccasionRecipient.name)).all()
    return [{"id": r.id, "name": r.name, "audience_type": r.audience_type, "venue_name": r.venue_name, "email": r.email, "phone": r.phone, "birthday": r.birthday, "active": r.active} for r in rows]


@router.post("/rules")
def create_rule(payload: RuleCreate, db: Session = Depends(get_db)):
    if payload.days_before < 0 or payload.days_before > 60:
        raise HTTPException(400, "Bildirim günü 0-60 arasında olmalıdır")
    x = OccasionRule(**payload.model_dump())
    db.add(x); db.commit(); db.refresh(x)
    return {"id": x.id}


@router.get("/rules")
def list_rules(db: Session = Depends(get_db)):
    rows = db.scalars(select(OccasionRule).order_by(OccasionRule.occasion_type, OccasionRule.days_before.desc())).all()
    return [{"id": x.id, "occasion_type": x.occasion_type, "days_before": x.days_before, "channel": x.channel, "target_audience": x.target_audience, "message_template": x.message_template, "enabled": x.enabled} for x in rows]


@router.get("/logs")
def list_logs(db: Session = Depends(get_db)):
    rows = db.scalars(select(OccasionLog).order_by(OccasionLog.sent_at.desc()).limit(250)).all()
    return [{"id": x.id, "occasion_key": x.occasion_key, "recipient_id": x.recipient_id, "channel": x.channel, "recipient": x.recipient, "status": x.status, "sent_at": x.sent_at, "payload": json.loads(x.payload)} for x in rows]
