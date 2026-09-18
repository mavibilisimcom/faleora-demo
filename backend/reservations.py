from __future__ import annotations
import os
from datetime import datetime,timezone
from fastapi import APIRouter,Depends,HTTPException
from pydantic import BaseModel
from sqlalchemy import Boolean,DateTime,Integer,String,Text,create_engine,select
from sqlalchemy.orm import DeclarativeBase,Mapped,Session,mapped_column,sessionmaker
DB=os.getenv("DATABASE_URL","sqlite:///./faleora.db");e=create_engine(DB,future=True,connect_args={"check_same_thread":False} if DB.startswith("sqlite") else {});S=sessionmaker(bind=e,autoflush=False,expire_on_commit=False)
class B(DeclarativeBase):pass
class Reservation(B):
 __tablename__="reservations";id:Mapped[int]=mapped_column(primary_key=True);venue_id:Mapped[int]=mapped_column(Integer,index=True);guest_ref:Mapped[str]=mapped_column(String(120),index=True);party_size:Mapped[int]=mapped_column(Integer);starts_at:Mapped[datetime]=mapped_column(DateTime(timezone=True),index=True);table_ref:Mapped[str]=mapped_column(String(80),default="");status:Mapped[str]=mapped_column(String(30),default="booked",index=True);notes:Mapped[str]=mapped_column(Text,default="");created_at:Mapped[datetime]=mapped_column(DateTime(timezone=True),default=lambda:datetime.now(timezone.utc))
class Waitlist(B):
 __tablename__="waitlist";id:Mapped[int]=mapped_column(primary_key=True);venue_id:Mapped[int]=mapped_column(Integer,index=True);guest_ref:Mapped[str]=mapped_column(String(120));party_size:Mapped[int]=mapped_column(Integer);status:Mapped[str]=mapped_column(String(30),default="waiting",index=True);created_at:Mapped[datetime]=mapped_column(DateTime(timezone=True),default=lambda:datetime.now(timezone.utc))
B.metadata.create_all(e);router=APIRouter(prefix="/api/reservations",tags=["reservations"])
def dbd():
 d=S()
 try:yield d
 finally:d.close()
class ResIn(BaseModel):venue_id:int;guest_ref:str;party_size:int;starts_at:datetime;table_ref:str="";notes:str=""
class WaitIn(BaseModel):venue_id:int;guest_ref:str;party_size:int
@router.post("")
def add(p:ResIn,db:Session=Depends(dbd)):
 if p.party_size<1:raise HTTPException(400,"Kişi sayısı geçersiz")
 x=Reservation(**p.model_dump());db.add(x);db.commit();db.refresh(x);return {"id":x.id,"status":x.status}
@router.get("/venue/{venue_id}")
def list_res(venue_id:int,db:Session=Depends(dbd)):
 return [{"id":x.id,"guest_ref":x.guest_ref,"party_size":x.party_size,"starts_at":x.starts_at,"table_ref":x.table_ref,"status":x.status} for x in db.scalars(select(Reservation).where(Reservation.venue_id==venue_id).order_by(Reservation.starts_at)).all()]
@router.post("/waitlist")
def wait(p:WaitIn,db:Session=Depends(dbd)):
 x=Waitlist(**p.model_dump());db.add(x);db.commit();db.refresh(x);return {"id":x.id,"status":x.status}
