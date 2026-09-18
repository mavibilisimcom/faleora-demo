from __future__ import annotations
import os
from datetime import datetime,timezone
from fastapi import APIRouter,Depends
from pydantic import BaseModel
from sqlalchemy import DateTime,Float,Integer,String,Text,create_engine,select
from sqlalchemy.orm import DeclarativeBase,Mapped,Session,mapped_column,sessionmaker
DB=os.getenv("DATABASE_URL","sqlite:///./faleora.db");e=create_engine(DB,future=True,connect_args={"check_same_thread":False} if DB.startswith("sqlite") else {});S=sessionmaker(bind=e,autoflush=False,expire_on_commit=False)
class B(DeclarativeBase):pass
class OpsEvent(B):
 __tablename__="ops_events";id:Mapped[int]=mapped_column(primary_key=True);venue_id:Mapped[int]=mapped_column(Integer,index=True);event_type:Mapped[str]=mapped_column(String(60),index=True);severity:Mapped[str]=mapped_column(String(20),default="info",index=True);source:Mapped[str]=mapped_column(String(40),default="system");message:Mapped[str]=mapped_column(Text);metric_value:Mapped[float|None]=mapped_column(Float,nullable=True);created_at:Mapped[datetime]=mapped_column(DateTime(timezone=True),default=lambda:datetime.now(timezone.utc),index=True)
class Checklist(B):
 __tablename__="ops_checklists";id:Mapped[int]=mapped_column(primary_key=True);venue_id:Mapped[int]=mapped_column(Integer,index=True);check_type:Mapped[str]=mapped_column(String(40),index=True);item:Mapped[str]=mapped_column(String(220));status:Mapped[str]=mapped_column(String(20),default="pending");staff_ref:Mapped[str]=mapped_column(String(120),default="");completed_at:Mapped[datetime|None]=mapped_column(DateTime(timezone=True),nullable=True)
B.metadata.create_all(e);router=APIRouter(prefix="/api/ops",tags=["operations"])
def dbd():
 d=S()
 try:yield d
 finally:d.close()
class EventIn(BaseModel):venue_id:int;event_type:str;severity:str="info";source:str="system";message:str;metric_value:float|None=None
class CheckIn(BaseModel):venue_id:int;check_type:str;item:str
@router.post("/events")
def event(p:EventIn,db:Session=Depends(dbd)):
 x=OpsEvent(**p.model_dump());db.add(x);db.commit();db.refresh(x);return {"id":x.id}
@router.get("/venues/{venue_id}/events")
def events(venue_id:int,db:Session=Depends(dbd)):
 rows=db.scalars(select(OpsEvent).where(OpsEvent.venue_id==venue_id).order_by(OpsEvent.created_at.desc()).limit(100)).all()
 return [{"id":x.id,"type":x.event_type,"severity":x.severity,"source":x.source,"message":x.message,"value":x.metric_value,"created_at":x.created_at} for x in rows]
@router.post("/checklists")
def check(p:CheckIn,db:Session=Depends(dbd)):
 x=Checklist(**p.model_dump());db.add(x);db.commit();db.refresh(x);return {"id":x.id}
@router.post("/checklists/{cid}/complete")
def complete(cid:int,staff_ref:str="",db:Session=Depends(dbd)):
 x=db.get(Checklist,cid)
 if not x:return {"ok":False}
 x.status="completed";x.staff_ref=staff_ref;x.completed_at=datetime.now(timezone.utc);db.commit();return {"ok":True}
