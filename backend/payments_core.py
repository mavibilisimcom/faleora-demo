from __future__ import annotations
import os
from datetime import datetime,timezone
from fastapi import APIRouter,Depends,HTTPException
from pydantic import BaseModel
from sqlalchemy import DateTime,Float,Integer,String,create_engine,select
from sqlalchemy.orm import DeclarativeBase,Mapped,Session,mapped_column,sessionmaker
DB=os.getenv("DATABASE_URL","sqlite:///./faleora.db");e=create_engine(DB,future=True,connect_args={"check_same_thread":False} if DB.startswith("sqlite") else {});S=sessionmaker(bind=e,autoflush=False,expire_on_commit=False)
class B(DeclarativeBase):pass
class Payment(B):
 __tablename__="pos_payments";id:Mapped[int]=mapped_column(primary_key=True);venue_id:Mapped[int]=mapped_column(Integer,index=True);order_id:Mapped[int]=mapped_column(Integer,index=True);method:Mapped[str]=mapped_column(String(30),index=True);amount:Mapped[float]=mapped_column(Float);status:Mapped[str]=mapped_column(String(20),default="captured",index=True);provider_ref:Mapped[str]=mapped_column(String(160),default="");created_at:Mapped[datetime]=mapped_column(DateTime(timezone=True),default=lambda:datetime.now(timezone.utc))
B.metadata.create_all(e);router=APIRouter(prefix="/api/payments",tags=["payments"])
def dbd():
 d=S()
 try:yield d
 finally:d.close()
class PayIn(BaseModel):venue_id:int;order_id:int;method:str;amount:float;provider_ref:str=""
@router.post("")
def pay(p:PayIn,db:Session=Depends(dbd)):
 if p.method not in {"cash","card","online","meal_card","other"} or p.amount<=0:raise HTTPException(400,"Ödeme geçersiz")
 x=Payment(**p.model_dump());db.add(x);db.commit();db.refresh(x);return {"id":x.id,"status":x.status}
@router.get("/orders/{order_id}")
def order_payments(order_id:int,db:Session=Depends(dbd)):
 rows=db.scalars(select(Payment).where(Payment.order_id==order_id,Payment.status=="captured")).all();return {"paid":sum(x.amount for x in rows),"payments":[{"id":x.id,"method":x.method,"amount":x.amount} for x in rows]}
