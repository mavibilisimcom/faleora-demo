from __future__ import annotations
import os,json
from datetime import datetime,timezone
from fastapi import APIRouter,Depends,HTTPException
from pydantic import BaseModel
from sqlalchemy import DateTime,Float,Integer,String,Text,create_engine,select
from sqlalchemy.orm import DeclarativeBase,Mapped,Session,mapped_column,sessionmaker
DB=os.getenv("DATABASE_URL","sqlite:///./faleora.db");e=create_engine(DB,future=True,connect_args={"check_same_thread":False} if DB.startswith("sqlite") else {},pool_pre_ping=True);S=sessionmaker(bind=e,autoflush=False,expire_on_commit=False)
class B(DeclarativeBase):pass
class Shift(B):
 __tablename__="pilot_cash_shifts";id:Mapped[int]=mapped_column(primary_key=True);venue_id:Mapped[int]=mapped_column(Integer,index=True);cashier_ref:Mapped[str]=mapped_column(String(120),index=True);opening_cash:Mapped[float]=mapped_column(Float,default=0);expected_cash:Mapped[float]=mapped_column(Float,default=0);counted_cash:Mapped[float|None]=mapped_column(Float,nullable=True);status:Mapped[str]=mapped_column(String(20),default="open",index=True);opened_at:Mapped[datetime]=mapped_column(DateTime(timezone=True),default=lambda:datetime.now(timezone.utc));closed_at:Mapped[datetime|None]=mapped_column(DateTime(timezone=True),nullable=True)
class CashEvent(B):
 __tablename__="pilot_cash_events";id:Mapped[int]=mapped_column(primary_key=True);shift_id:Mapped[int]=mapped_column(Integer,index=True);event_type:Mapped[str]=mapped_column(String(30));amount:Mapped[float]=mapped_column(Float);reference:Mapped[str]=mapped_column(String(120),default="");created_at:Mapped[datetime]=mapped_column(DateTime(timezone=True),default=lambda:datetime.now(timezone.utc))
B.metadata.create_all(e);router=APIRouter(prefix="/api/cash",tags=["cash-reconciliation"])
def dbd():
 d=S()
 try:yield d
 finally:d.close()
class OpenIn(BaseModel):venue_id:int;cashier_ref:str;opening_cash:float=0
class EventIn(BaseModel):event_type:str;amount:float;reference:str=""
class CloseIn(BaseModel):counted_cash:float
@router.post("/shifts")
def open_shift(p:OpenIn,db:Session=Depends(dbd)):
 old=db.scalar(select(Shift).where(Shift.venue_id==p.venue_id,Shift.cashier_ref==p.cashier_ref,Shift.status=="open"))
 if old:return {"id":old.id,"status":"open","existing":True}
 x=Shift(**p.model_dump(),expected_cash=p.opening_cash);db.add(x);db.commit();db.refresh(x);return {"id":x.id,"status":x.status}
@router.post("/shifts/{sid}/events")
def event(sid:int,p:EventIn,db:Session=Depends(dbd)):
 s=db.get(Shift,sid)
 if not s or s.status!="open":raise HTTPException(409,"Açık vardiya bulunamadı")
 if p.event_type not in {"cash_sale","cash_refund","cash_in","cash_out"} or p.amount<=0:raise HTTPException(400,"Kasa hareketi geçersiz")
 sign=1 if p.event_type in {"cash_sale","cash_in"} else -1;s.expected_cash=round(s.expected_cash+sign*p.amount,2);db.add(CashEvent(shift_id=sid,**p.model_dump()));db.commit();return {"expected_cash":s.expected_cash}
@router.post("/shifts/{sid}/close")
def close(sid:int,p:CloseIn,db:Session=Depends(dbd)):
 s=db.get(Shift,sid)
 if not s or s.status!="open":raise HTTPException(409,"Açık vardiya bulunamadı")
 s.counted_cash=p.counted_cash;s.status="closed";s.closed_at=datetime.now(timezone.utc);db.commit();return {"id":s.id,"expected_cash":s.expected_cash,"counted_cash":s.counted_cash,"difference":round(s.counted_cash-s.expected_cash,2),"status":s.status}
