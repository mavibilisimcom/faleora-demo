from __future__ import annotations
import os,json
from datetime import datetime,timezone
from fastapi import APIRouter,Depends,HTTPException
from pydantic import BaseModel
from sqlalchemy import DateTime,Float,Integer,String,Text,create_engine,select
from sqlalchemy.orm import DeclarativeBase,Mapped,Session,mapped_column,sessionmaker
from decimal import Decimal
from transaction_service import CheckoutInput,CheckoutError,validate_checkout
DB=os.getenv("DATABASE_URL","sqlite:///./faleora.db");e=create_engine(DB,future=True,connect_args={"check_same_thread":False} if DB.startswith("sqlite") else {});S=sessionmaker(bind=e,autoflush=False,expire_on_commit=False)
class B(DeclarativeBase):pass
class Finalization(B):
 __tablename__="order_finalizations";id:Mapped[int]=mapped_column(primary_key=True);venue_id:Mapped[int]=mapped_column(Integer,index=True);order_id:Mapped[int]=mapped_column(Integer,unique=True,index=True);order_total:Mapped[float]=mapped_column(Float);paid_total:Mapped[float]=mapped_column(Float);stock_cost:Mapped[float]=mapped_column(Float,default=0);reward_amount:Mapped[int]=mapped_column(Integer,default=0);status:Mapped[str]=mapped_column(String(30),default="closed");summary:Mapped[str]=mapped_column(Text,default="{}");created_at:Mapped[datetime]=mapped_column(DateTime(timezone=True),default=lambda:datetime.now(timezone.utc))
B.metadata.create_all(e);router=APIRouter(prefix="/api/checkout",tags=["checkout"])
def dbd():
 d=S()
 try:yield d
 finally:d.close()
class FinalizeIn(BaseModel):venue_id:int;order_id:int;order_total:float;paid_total:float;stock_cost:float=0;reward_amount:int=0;actor_ref:str="system";items:int=0
@router.post("/finalize")
def finalize(p:FinalizeIn,db:Session=Depends(dbd)):
 if db.scalar(select(Finalization).where(Finalization.order_id==p.order_id)):raise HTTPException(409,"Adisyon daha önce kapatıldı")
 try: result=validate_checkout(CheckoutInput(p.order_id,Decimal(str(p.order_total)),Decimal(str(p.paid_total)),Decimal(str(p.stock_cost)),p.reward_amount))
 except CheckoutError as exc:raise HTTPException(409,str(exc))
 x=Finalization(venue_id=p.venue_id,order_id=p.order_id,order_total=p.order_total,paid_total=p.paid_total,stock_cost=p.stock_cost,reward_amount=p.reward_amount,summary=json.dumps({"actor":p.actor_ref,"items":p.items,"closed_at":datetime.now(timezone.utc).isoformat()}));db.add(x);db.commit();db.refresh(x)
 return {"id":x.id,"status":"closed","gross_margin":float(result["gross_margin"]),"change":float(result["change"]),"reward":p.reward_amount}
@router.get("/{order_id}")
def status(order_id:int,db:Session=Depends(dbd)):
 x=db.scalar(select(Finalization).where(Finalization.order_id==order_id))
 if not x:return {"status":"open"}
 return {"status":x.status,"order_total":x.order_total,"paid_total":x.paid_total,"stock_cost":x.stock_cost,"reward":x.reward_amount}
