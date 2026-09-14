from __future__ import annotations
import os
from datetime import date, datetime, timezone
from typing import Optional
from fastapi import APIRouter, Depends
from pydantic import BaseModel
from sqlalchemy import Boolean, Date, DateTime, String, Text, create_engine, select
from sqlalchemy.orm import DeclarativeBase, Mapped, Session, mapped_column, sessionmaker
DB=os.getenv('DATABASE_URL','sqlite:///./faleora.db');engine=create_engine(DB,future=True,connect_args={'check_same_thread':False} if DB.startswith('sqlite') else {});SessionLocal=sessionmaker(bind=engine,autoflush=False,expire_on_commit=False)
class Base(DeclarativeBase): pass
class UserProfile(Base):
 __tablename__='user_profiles';user_ref:Mapped[str]=mapped_column(String(120),primary_key=True);display_name:Mapped[Optional[str]]=mapped_column(String(120),nullable=True);birth_date:Mapped[Optional[date]]=mapped_column(Date,nullable=True);city:Mapped[Optional[str]]=mapped_column(String(120),nullable=True);language:Mapped[str]=mapped_column(String(10),default='tr');tier:Mapped[str]=mapped_column(String(20),default='free');updated_at:Mapped[datetime]=mapped_column(DateTime(timezone=True),default=lambda:datetime.now(timezone.utc))
class Consent(Base):
 __tablename__='user_consents';id:Mapped[int]=mapped_column(primary_key=True);user_ref:Mapped[str]=mapped_column(String(120),index=True);key:Mapped[str]=mapped_column(String(80),index=True);enabled:Mapped[bool]=mapped_column(Boolean,default=False);updated_at:Mapped[datetime]=mapped_column(DateTime(timezone=True),default=lambda:datetime.now(timezone.utc))
class ArchiveItem(Base):
 __tablename__='user_archive';id:Mapped[int]=mapped_column(primary_key=True);user_ref:Mapped[str]=mapped_column(String(120),index=True);item_type:Mapped[str]=mapped_column(String(40),index=True);title:Mapped[str]=mapped_column(String(180));body:Mapped[str]=mapped_column(Text,default='');favorite:Mapped[bool]=mapped_column(Boolean,default=False);created_at:Mapped[datetime]=mapped_column(DateTime(timezone=True),default=lambda:datetime.now(timezone.utc))
Base.metadata.create_all(engine);router=APIRouter(prefix='/api/users',tags=['users'])
def dbd():
 d=SessionLocal()
 try: yield d
 finally:d.close()
class ProfileIn(BaseModel): display_name:Optional[str]=None;birth_date:Optional[date]=None;city:Optional[str]=None;language:str='tr';tier:str='free'
class ConsentIn(BaseModel): key:str;enabled:bool
class ArchiveIn(BaseModel): item_type:str;title:str;body:str='';favorite:bool=False
@router.put('/{u}/profile')
def profile(u:str,p:ProfileIn,db:Session=Depends(dbd)):
 x=db.get(UserProfile,u) or UserProfile(user_ref=u);[setattr(x,k,v) for k,v in p.model_dump().items()];x.updated_at=datetime.now(timezone.utc);db.add(x);db.commit();return {'ok':True}
@router.get('/{u}/profile')
def get_profile(u:str,db:Session=Depends(dbd)):
 x=db.get(UserProfile,u);return None if not x else {'user_ref':x.user_ref,'display_name':x.display_name,'birth_date':x.birth_date,'city':x.city,'language':x.language,'tier':x.tier}
@router.put('/{u}/consent')
def consent(u:str,p:ConsentIn,db:Session=Depends(dbd)):
 x=db.scalar(select(Consent).where(Consent.user_ref==u,Consent.key==p.key)) or Consent(user_ref=u,key=p.key);x.enabled=p.enabled;x.updated_at=datetime.now(timezone.utc);db.add(x);db.commit();return {'ok':True}
@router.get('/{u}/consents')
def consents(u:str,db:Session=Depends(dbd)):
 return [{'key':x.key,'enabled':x.enabled} for x in db.scalars(select(Consent).where(Consent.user_ref==u)).all()]
@router.post('/{u}/archive')
def archive(u:str,p:ArchiveIn,db:Session=Depends(dbd)):
 x=ArchiveItem(user_ref=u,**p.model_dump());db.add(x);db.commit();db.refresh(x);return {'id':x.id}
@router.get('/{u}/archive')
def archive_list(u:str,db:Session=Depends(dbd)):
 return [{'id':x.id,'type':x.item_type,'title':x.title,'favorite':x.favorite,'created_at':x.created_at} for x in db.scalars(select(ArchiveItem).where(ArchiveItem.user_ref==u).order_by(ArchiveItem.created_at.desc())).all()]
