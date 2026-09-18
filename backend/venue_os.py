from __future__ import annotations
import os,secrets
from datetime import datetime,timezone
from fastapi import APIRouter,Depends,HTTPException
from pydantic import BaseModel
from sqlalchemy import DateTime,Integer,String,create_engine,select
from sqlalchemy.orm import DeclarativeBase,Mapped,Session,mapped_column,sessionmaker
DB=os.getenv("DATABASE_URL","sqlite:///./faleora.db");e=create_engine(DB,future=True,connect_args={"check_same_thread":False} if DB.startswith("sqlite") else {});S=sessionmaker(bind=e,autoflush=False,expire_on_commit=False)
class B(DeclarativeBase):pass
class Table(B):
 __tablename__="venue_tables";id:Mapped[int]=mapped_column(primary_key=True);venue_id:Mapped[int]=mapped_column(Integer,index=True);label:Mapped[str]=mapped_column(String(60));public_code:Mapped[str]=mapped_column(String(24),unique=True,index=True);active:Mapped[int]=mapped_column(Integer,default=1)
class ServiceRequest(B):
 __tablename__="service_requests";id:Mapped[int]=mapped_column(primary_key=True);table_id:Mapped[int]=mapped_column(Integer,index=True);request_type:Mapped[str]=mapped_column(String(40),index=True);status:Mapped[str]=mapped_column(String(30),default="open",index=True);created_at:Mapped[datetime]=mapped_column(DateTime(timezone=True),default=lambda:datetime.now(timezone.utc));completed_at:Mapped[datetime|None]=mapped_column(DateTime(timezone=True),nullable=True)
class Feedback(B):
 __tablename__="venue_feedback";id:Mapped[int]=mapped_column(primary_key=True);venue_id:Mapped[int]=mapped_column(Integer,index=True);visit_ref:Mapped[str]=mapped_column(String(120),index=True);rating:Mapped[int]=mapped_column(Integer);service:Mapped[int]=mapped_column(Integer);food:Mapped[int]=mapped_column(Integer);atmosphere:Mapped[int]=mapped_column(Integer);comment:Mapped[str]=mapped_column(String(1000),default="");created_at:Mapped[datetime]=mapped_column(DateTime(timezone=True),default=lambda:datetime.now(timezone.utc))
B.metadata.create_all(e);router=APIRouter(prefix="/api/venue-os",tags=["venue-os"])
def dbd():
 d=S()
 try:yield d
 finally:d.close()
class TableIn(BaseModel):venue_id:int;label:str
class RequestIn(BaseModel):request_type:str
class FeedbackIn(BaseModel):venue_id:int;visit_ref:str;rating:int;service:int;food:int;atmosphere:int;comment:str=""
@router.post("/tables")
def table(p:TableIn,db:Session=Depends(dbd)):
 x=Table(**p.model_dump(),public_code=secrets.token_urlsafe(9));db.add(x);db.commit();db.refresh(x);return {"id":x.id,"code":x.public_code}
@router.post("/tables/{code}/requests")
def request(code:str,p:RequestIn,db:Session=Depends(dbd)):
 t=db.scalar(select(Table).where(Table.public_code==code,Table.active==1))
 if not t:raise HTTPException(404,"Masa bulunamadı")
 if p.request_type not in {"waiter","bill","water","other"}:raise HTTPException(400,"Geçersiz talep")
 x=ServiceRequest(table_id=t.id,request_type=p.request_type);db.add(x);db.commit();db.refresh(x);return {"id":x.id,"status":x.status}
@router.get("/venues/{venue_id}/requests")
def requests(venue_id:int,db:Session=Depends(dbd)):
 tids=[x.id for x in db.scalars(select(Table).where(Table.venue_id==venue_id)).all()]
 if not tids:return []
 rows=db.scalars(select(ServiceRequest).where(ServiceRequest.table_id.in_(tids),ServiceRequest.status=="open").order_by(ServiceRequest.created_at)).all()
 return [{"id":x.id,"table_id":x.table_id,"type":x.request_type,"status":x.status,"created_at":x.created_at} for x in rows]
@router.post("/requests/{rid}/complete")
def complete(rid:int,db:Session=Depends(dbd)):
 x=db.get(ServiceRequest,rid)
 if not x:raise HTTPException(404,"Talep bulunamadı")
 x.status="completed";x.completed_at=datetime.now(timezone.utc);db.commit();return {"ok":True}
@router.post("/feedback")
def feedback(p:FeedbackIn,db:Session=Depends(dbd)):
 vals=[p.rating,p.service,p.food,p.atmosphere]
 if any(v<1 or v>5 for v in vals):raise HTTPException(400,"Puanlar 1-5 arasında olmalı")
 x=Feedback(**p.model_dump());db.add(x);db.commit();db.refresh(x);return {"id":x.id}
