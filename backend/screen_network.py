from __future__ import annotations
import os,secrets
from datetime import datetime,timezone
from typing import Optional
from fastapi import APIRouter,Depends,HTTPException
from pydantic import BaseModel
from sqlalchemy import Boolean,DateTime,Integer,String,Text,create_engine,select
from sqlalchemy.orm import DeclarativeBase,Mapped,Session,mapped_column,sessionmaker
DB=os.getenv("DATABASE_URL","sqlite:///./faleora.db")
e=create_engine(DB,future=True,connect_args={"check_same_thread":False} if DB.startswith("sqlite") else {})
S=sessionmaker(bind=e,autoflush=False,expire_on_commit=False)
class B(DeclarativeBase):pass
class Screen(B):
 __tablename__="screens"
 id:Mapped[int]=mapped_column(primary_key=True)
 venue_id:Mapped[int]=mapped_column(Integer,index=True)
 name:Mapped[str]=mapped_column(String(120))
 pair_code:Mapped[str]=mapped_column(String(12),unique=True,index=True)
 status:Mapped[str]=mapped_column(String(20),default="offline")
 playlist:Mapped[str]=mapped_column(String(80),default="default")
 last_seen:Mapped[Optional[datetime]]=mapped_column(DateTime(timezone=True),nullable=True)
class ScreenEvent(B):
 __tablename__="screen_events"
 id:Mapped[int]=mapped_column(primary_key=True)
 screen_id:Mapped[int]=mapped_column(Integer,index=True)
 event_type:Mapped[str]=mapped_column(String(40),index=True)
 payload:Mapped[str]=mapped_column(Text,default="{}")
 approved:Mapped[bool]=mapped_column(Boolean,default=False)
 created_at:Mapped[datetime]=mapped_column(DateTime(timezone=True),default=lambda:datetime.now(timezone.utc))
B.metadata.create_all(e)
router=APIRouter(prefix="/api/screens",tags=["screens"])
def dbd():
 d=S()
 try:yield d
 finally:d.close()
class ScreenIn(BaseModel):
 venue_id:int
 name:str
 playlist:str="default"
class EventIn(BaseModel):
 event_type:str
 payload:str="{}"
 approved:bool=False
@router.post("")
def add(p:ScreenIn,db:Session=Depends(dbd)):
 x=Screen(**p.model_dump(),pair_code=str(secrets.randbelow(900000)+100000));db.add(x);db.commit();db.refresh(x);return {"id":x.id,"pair_code":x.pair_code}
@router.get("")
def listing(db:Session=Depends(dbd)):
 return [{"id":x.id,"venue_id":x.venue_id,"name":x.name,"status":x.status,"playlist":x.playlist,"last_seen":x.last_seen} for x in db.scalars(select(Screen)).all()]
@router.post("/{sid}/heartbeat")
def heartbeat(sid:int,db:Session=Depends(dbd)):
 x=db.get(Screen,sid)
 if not x:raise HTTPException(404,"Ekran bulunamadı")
 x.status="online";x.last_seen=datetime.now(timezone.utc);db.commit();return {"ok":True}
@router.post("/{sid}/events")
def event(sid:int,p:EventIn,db:Session=Depends(dbd)):
 if not db.get(Screen,sid):raise HTTPException(404,"Ekran bulunamadı")
 x=ScreenEvent(screen_id=sid,**p.model_dump());db.add(x);db.commit();db.refresh(x);return {"id":x.id,"approved":x.approved}
@router.get("/{sid}/events")
def events(sid:int,approved:Optional[bool]=None,db:Session=Depends(dbd)):
 q=select(ScreenEvent).where(ScreenEvent.screen_id==sid)
 if approved is not None:q=q.where(ScreenEvent.approved==approved)
 return [{"id":x.id,"type":x.event_type,"payload":x.payload,"approved":x.approved} for x in db.scalars(q.order_by(ScreenEvent.created_at.desc())).all()]
