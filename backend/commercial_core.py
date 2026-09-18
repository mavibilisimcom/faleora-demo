from __future__ import annotations
import os
from datetime import datetime,timezone
from fastapi import APIRouter,Depends,HTTPException
from pydantic import BaseModel
from sqlalchemy import DateTime,Float,Integer,String,Text,create_engine,select
from sqlalchemy.orm import DeclarativeBase,Mapped,Session,mapped_column,sessionmaker
DB=os.getenv("DATABASE_URL","sqlite:///./faleora.db");e=create_engine(DB,future=True,connect_args={"check_same_thread":False} if DB.startswith("sqlite") else {});S=sessionmaker(bind=e,autoflush=False,expire_on_commit=False)
class B(DeclarativeBase):pass
class StockMovement(B):
 __tablename__="stock_movements";id:Mapped[int]=mapped_column(primary_key=True);venue_id:Mapped[int]=mapped_column(Integer,index=True);stock_item_id:Mapped[int]=mapped_column(Integer,index=True);movement_type:Mapped[str]=mapped_column(String(40),index=True);qty:Mapped[float]=mapped_column(Float);unit_cost:Mapped[float]=mapped_column(Float,default=0);reference:Mapped[str]=mapped_column(String(120),default="");created_at:Mapped[datetime]=mapped_column(DateTime(timezone=True),default=lambda:datetime.now(timezone.utc),index=True)
class Audit(B):
 __tablename__="audit_events";id:Mapped[int]=mapped_column(primary_key=True);venue_id:Mapped[int]=mapped_column(Integer,index=True);actor_ref:Mapped[str]=mapped_column(String(120),index=True);action:Mapped[str]=mapped_column(String(80),index=True);entity:Mapped[str]=mapped_column(String(80));entity_ref:Mapped[str]=mapped_column(String(120));details:Mapped[str]=mapped_column(Text,default="");created_at:Mapped[datetime]=mapped_column(DateTime(timezone=True),default=lambda:datetime.now(timezone.utc),index=True)
class CashShift(B):
 __tablename__="cash_shifts";id:Mapped[int]=mapped_column(primary_key=True);venue_id:Mapped[int]=mapped_column(Integer,index=True);staff_ref:Mapped[str]=mapped_column(String(120),index=True);opening_cash:Mapped[float]=mapped_column(Float);closing_cash:Mapped[float|None]=mapped_column(Float,nullable=True);status:Mapped[str]=mapped_column(String(20),default="open",index=True);opened_at:Mapped[datetime]=mapped_column(DateTime(timezone=True),default=lambda:datetime.now(timezone.utc));closed_at:Mapped[datetime|None]=mapped_column(DateTime(timezone=True),nullable=True)
B.metadata.create_all(e);router=APIRouter(prefix="/api/core",tags=["commercial-core"])
def dbd():
 d=S()
 try:yield d
 finally:d.close()
class MoveIn(BaseModel):venue_id:int;stock_item_id:int;movement_type:str;qty:float;unit_cost:float=0;reference:str=""
class AuditIn(BaseModel):venue_id:int;actor_ref:str;action:str;entity:str;entity_ref:str;details:str=""
class ShiftIn(BaseModel):venue_id:int;staff_ref:str;opening_cash:float=0
@router.post("/stock-movements")
def move(p:MoveIn,db:Session=Depends(dbd)):
 allowed={"purchase","sale","waste","transfer_in","transfer_out","count_adjustment","return"}
 if p.movement_type not in allowed:raise HTTPException(400,"Geçersiz stok hareketi")
 x=StockMovement(**p.model_dump());db.add(x);db.commit();db.refresh(x);return {"id":x.id}
@router.get("/stock/{venue_id}/{item_id}/balance")
def balance(venue_id:int,item_id:int,db:Session=Depends(dbd)):
 rows=db.scalars(select(StockMovement).where(StockMovement.venue_id==venue_id,StockMovement.stock_item_id==item_id)).all()
 return {"balance":sum(x.qty for x in rows),"movements":len(rows)}
@router.post("/audit")
def audit(p:AuditIn,db:Session=Depends(dbd)):
 x=Audit(**p.model_dump());db.add(x);db.commit();return {"ok":True}
@router.post("/shifts")
def shift(p:ShiftIn,db:Session=Depends(dbd)):
 x=CashShift(**p.model_dump());db.add(x);db.commit();db.refresh(x);return {"id":x.id,"status":x.status}
@router.post("/shifts/{sid}/close")
def close(sid:int,closing_cash:float,db:Session=Depends(dbd)):
 x=db.get(CashShift,sid)
 if not x or x.status!="open":raise HTTPException(404,"Açık vardiya bulunamadı")
 x.closing_cash=closing_cash;x.status="closed";x.closed_at=datetime.now(timezone.utc);db.commit();return {"ok":True}
