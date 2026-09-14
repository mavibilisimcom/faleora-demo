from __future__ import annotations

import re
from datetime import datetime, timezone
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy import Boolean, DateTime, Integer, String, Text, create_engine, select
from sqlalchemy.orm import DeclarativeBase, Mapped, Session, mapped_column, sessionmaker

import os

DATABASE_URL = os.getenv("DATABASE_URL", "sqlite:///./faleora.db")
connect_args = {"check_same_thread": False} if DATABASE_URL.startswith("sqlite") else {}
engine = create_engine(DATABASE_URL, future=True, connect_args=connect_args)
SessionLocal = sessionmaker(bind=engine, autoflush=False, expire_on_commit=False)


class Base(DeclarativeBase):
    pass


class VenueProfile(Base):
    __tablename__ = "venue_profiles"
    id: Mapped[int] = mapped_column(primary_key=True)
    venue_name: Mapped[str] = mapped_column(String(160), index=True)
    slug: Mapped[str] = mapped_column(String(180), unique=True, index=True)
    tagline: Mapped[Optional[str]] = mapped_column(String(240), nullable=True)
    description: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    city: Mapped[Optional[str]] = mapped_column(String(100), nullable=True, index=True)
    district: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    address: Mapped[Optional[str]] = mapped_column(String(300), nullable=True)
    phone: Mapped[Optional[str]] = mapped_column(String(60), nullable=True)
    website: Mapped[Optional[str]] = mapped_column(String(300), nullable=True)
    instagram: Mapped[Optional[str]] = mapped_column(String(200), nullable=True)
    opening_hours: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    amenities: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    menu_json: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    campaigns_json: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    events_json: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    gallery_json: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    status: Mapped[str] = mapped_column(String(30), default="draft", index=True)
    verified: Mapped[bool] = mapped_column(Boolean, default=False)
    featured: Mapped[bool] = mapped_column(Boolean, default=False)
    moderation_note: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), onupdate=lambda: datetime.now(timezone.utc))


class VenueProfileAudit(Base):
    __tablename__ = "venue_profile_audit"
    id: Mapped[int] = mapped_column(primary_key=True)
    profile_id: Mapped[int] = mapped_column(Integer, index=True)
    action: Mapped[str] = mapped_column(String(60))
    actor: Mapped[str] = mapped_column(String(100), default="demo-admin")
    note: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))


Base.metadata.create_all(engine)
router = APIRouter(prefix="/api/venue-profiles", tags=["venue-profiles"])


class ProfileIn(BaseModel):
    venue_name: str
    slug: Optional[str] = None
    tagline: Optional[str] = None
    description: Optional[str] = None
    city: Optional[str] = None
    district: Optional[str] = None
    address: Optional[str] = None
    phone: Optional[str] = None
    website: Optional[str] = None
    instagram: Optional[str] = None
    opening_hours: Optional[str] = None
    amenities: Optional[str] = None
    menu_json: Optional[str] = None
    campaigns_json: Optional[str] = None
    events_json: Optional[str] = None
    gallery_json: Optional[str] = None


class ModerationIn(BaseModel):
    status: str
    verified: Optional[bool] = None
    featured: Optional[bool] = None
    note: Optional[str] = None
    actor: str = "demo-admin"


def db_dep():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def slugify(value: str) -> str:
    value = value.lower().strip()
    table = str.maketrans("çğıöşü", "cgiosu")
    value = value.translate(table)
    value = re.sub(r"[^a-z0-9]+", "-", value).strip("-")
    return value or "mekan"


def serialize(x: VenueProfile) -> dict:
    return {
        "id": x.id,
        "venue_name": x.venue_name,
        "slug": x.slug,
        "tagline": x.tagline,
        "description": x.description,
        "city": x.city,
        "district": x.district,
        "address": x.address,
        "phone": x.phone,
        "website": x.website,
        "instagram": x.instagram,
        "opening_hours": x.opening_hours,
        "amenities": x.amenities,
        "menu_json": x.menu_json,
        "campaigns_json": x.campaigns_json,
        "events_json": x.events_json,
        "gallery_json": x.gallery_json,
        "status": x.status,
        "verified": x.verified,
        "featured": x.featured,
        "moderation_note": x.moderation_note,
        "created_at": x.created_at,
        "updated_at": x.updated_at,
    }


@router.get("")
def list_profiles(status: Optional[str] = None, city: Optional[str] = None, db: Session = Depends(db_dep)):
    stmt = select(VenueProfile).order_by(VenueProfile.updated_at.desc())
    if status:
        stmt = stmt.where(VenueProfile.status == status)
    if city:
        stmt = stmt.where(VenueProfile.city == city)
    return [serialize(x) for x in db.scalars(stmt).all()]


@router.get("/public/{slug}")
def public_profile(slug: str, db: Session = Depends(db_dep)):
    x = db.scalar(select(VenueProfile).where(VenueProfile.slug == slug, VenueProfile.status == "published"))
    if not x:
        raise HTTPException(404, "Yayınlanmış mekân profili bulunamadı")
    return serialize(x)


@router.get("/{profile_id}")
def get_profile(profile_id: int, db: Session = Depends(db_dep)):
    x = db.get(VenueProfile, profile_id)
    if not x:
        raise HTTPException(404, "Mekân profili bulunamadı")
    return serialize(x)


@router.post("")
def create_profile(payload: ProfileIn, db: Session = Depends(db_dep)):
    base_slug = slugify(payload.slug or payload.venue_name)
    slug = base_slug
    suffix = 2
    while db.scalar(select(VenueProfile.id).where(VenueProfile.slug == slug)):
        slug = f"{base_slug}-{suffix}"
        suffix += 1
    data = payload.model_dump()
    data["slug"] = slug
    x = VenueProfile(**data)
    db.add(x)
    db.commit()
    db.refresh(x)
    db.add(VenueProfileAudit(profile_id=x.id, action="created", actor="business-owner"))
    db.commit()
    return serialize(x)


@router.put("/{profile_id}")
def update_profile(profile_id: int, payload: ProfileIn, db: Session = Depends(db_dep)):
    x = db.get(VenueProfile, profile_id)
    if not x:
        raise HTTPException(404, "Mekân profili bulunamadı")
    for key, value in payload.model_dump(exclude={"slug"}).items():
        setattr(x, key, value)
    if payload.slug:
        wanted = slugify(payload.slug)
        other = db.scalar(select(VenueProfile.id).where(VenueProfile.slug == wanted, VenueProfile.id != x.id))
        if other:
            raise HTTPException(409, "Slug kullanımda")
        x.slug = wanted
    if x.status == "published":
        x.status = "pending_review"
    db.add(VenueProfileAudit(profile_id=x.id, action="updated", actor="business-owner"))
    db.commit()
    db.refresh(x)
    return serialize(x)


@router.post("/{profile_id}/submit")
def submit_profile(profile_id: int, db: Session = Depends(db_dep)):
    x = db.get(VenueProfile, profile_id)
    if not x:
        raise HTTPException(404, "Mekân profili bulunamadı")
    x.status = "pending_review"
    db.add(VenueProfileAudit(profile_id=x.id, action="submitted", actor="business-owner"))
    db.commit()
    return serialize(x)


@router.post("/{profile_id}/moderate")
def moderate_profile(profile_id: int, payload: ModerationIn, db: Session = Depends(db_dep)):
    allowed = {"draft", "pending_review", "published", "suspended", "rejected"}
    if payload.status not in allowed:
        raise HTTPException(400, "Geçersiz durum")
    x = db.get(VenueProfile, profile_id)
    if not x:
        raise HTTPException(404, "Mekân profili bulunamadı")
    x.status = payload.status
    if payload.verified is not None:
        x.verified = payload.verified
    if payload.featured is not None:
        x.featured = payload.featured
    x.moderation_note = payload.note
    db.add(VenueProfileAudit(profile_id=x.id, action=f"moderated:{payload.status}", actor=payload.actor, note=payload.note))
    db.commit()
    db.refresh(x)
    return serialize(x)


@router.get("/{profile_id}/audit")
def profile_audit(profile_id: int, db: Session = Depends(db_dep)):
    rows = db.scalars(select(VenueProfileAudit).where(VenueProfileAudit.profile_id == profile_id).order_by(VenueProfileAudit.created_at.desc())).all()
    return [{"id": r.id, "action": r.action, "actor": r.actor, "note": r.note, "created_at": r.created_at} for r in rows]
