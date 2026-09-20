from __future__ import annotations
import os,json
from datetime import datetime,timezone
from fastapi import APIRouter,Depends,HTTPException
from pydantic import BaseModel
from sqlalchemy import DateTime,Integer,String,Text,UniqueConstraint,create_engine,select
from sqlalchemy.orm import DeclarativeBase,Mapped,Session,mapped_column,sessionmaker
DB=os.getenv("DATABASE_URL","sqlite:///./faleora.db");e=create_engine(DB,future=True,connect_args={"check_same_thread":False} if DB.startswith("sqlite") else {},pool_pre_ping=True);S=sessionmaker(bind=e,autoflush=False,expire_on_commit=False)
class B(DeclarativeBase):pass
class SyncEvent(B):
 __tablename__="offline_sync_events";__table_args__=(UniqueConstraint("client_event_id",name="uq_offline_client_event"),)
 id:Mapped[int]=mapped_column(primary_key=True);client_event_id:Mapped[str]=mapped_column(String(120),index=True);venue_id:Mapped[int]=mapped_column(Integer,index=True);device_id:Mapped[str]=mapped_column(String(120),index=True);event_type:Mapped[str]=mapped_column(String(60),index=True);payload:Mapped[str]=mapped_column(Text);status:Mapped[str]=mapped_column(String(20),default="accepted");created_at:Mapped[datetime]=mapped_column(DateTime(timezone=True),default=lambda:datetime.now(timezone.utc))
B.metadata.create_all(e);router=APIRouter(prefix="/api/sync",tags=["offline-sync"])
def dbd():
 d=S()
 try:yield d
 finally:d.close()
class EventIn(BaseModel):client_event_id:str;venue_id:int;device_id:str;event_type:str;payload:dict
@router.post("/events")
def ingest(p:EventIn,db:Session=Depends(dbd)):
 old=db.scalar(select(SyncEvent).where(SyncEvent.client_event_id==p.client_event_id))
 if old:return {"id":old.id,"status":"duplicate","client_event_id":p.client_event_id}
 x=SyncEvent(client_event_id=p.client_event_id,venue_id=p.venue_id,device_id=p.device_id,event_type=p.event_type,payload=json.dumps(p.payload,ensure_ascii=False));db.add(x);db.commit();db.refresh(x);return {"id":x.id,"status":"accepted","client_event_id":x.client_event_id}
@router.get("/venues/{venue_id}/events")
def events(venue_id:int,db:Session=Depends(dbd)):
 rows=db.scalars(select(SyncEvent).where(SyncEvent.venue_id==venue_id).order_by(SyncEvent.id.desc()).limit(200)).all();return [{"id":x.id,"client_event_id":x.client_event_id,"device_id":x.device_id,"event_type":x.event_type,"status":x.status,"created_at":x.created_at} for x in rows]
