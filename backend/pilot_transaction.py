from __future__ import annotations
import json,os
from datetime import datetime,timezone
from fastapi import APIRouter,Depends,HTTPException
from pydantic import BaseModel
from sqlalchemy import DateTime,Float,Integer,String,Text,UniqueConstraint,create_engine,select
from sqlalchemy.orm import DeclarativeBase,Mapped,Session,mapped_column,sessionmaker
DB=os.getenv("DATABASE_URL","sqlite:///./faleora.db");e=create_engine(DB,future=True,connect_args={"check_same_thread":False} if DB.startswith("sqlite") else {},pool_pre_ping=True);S=sessionmaker(bind=e,autoflush=False,expire_on_commit=False)
class B(DeclarativeBase):pass
class Tx(B):
 __tablename__="pilot_transactions";__table_args__=(UniqueConstraint("client_ref",name="uq_pilot_tx_ref"),)
 id:Mapped[int]=mapped_column(primary_key=True);client_ref:Mapped[str]=mapped_column(String(120),index=True);venue_id:Mapped[int]=mapped_column(Integer,index=True);shift_id:Mapped[int|None]=mapped_column(Integer,nullable=True,index=True);actor_ref:Mapped[str]=mapped_column(String(120));status:Mapped[str]=mapped_column(String(30),default="closed");total:Mapped[float]=mapped_column(Float);paid:Mapped[float]=mapped_column(Float);stock_cost:Mapped[float]=mapped_column(Float,default=0);reward:Mapped[int]=mapped_column(Integer,default=0);payload:Mapped[str]=mapped_column(Text,default="{}");created_at:Mapped[datetime]=mapped_column(DateTime(timezone=True),default=lambda:datetime.now(timezone.utc))
class Event(B):
 __tablename__="pilot_transaction_events";id:Mapped[int]=mapped_column(primary_key=True);transaction_id:Mapped[int]=mapped_column(Integer,index=True);event_type:Mapped[str]=mapped_column(String(60),index=True);payload:Mapped[str]=mapped_column(Text,default="{}");created_at:Mapped[datetime]=mapped_column(DateTime(timezone=True),default=lambda:datetime.now(timezone.utc))
B.metadata.create_all(e);router=APIRouter(prefix="/api/pilot-transaction",tags=["pilot-transaction"])
def dbd():
 d=S()
 try:yield d
 finally:d.close()
class Item(BaseModel):product_id:int;name:str;qty:int=1;unit_price:float;modifiers:list[dict]=[]
class Payment(BaseModel):method:str;amount:float
class Finalize(BaseModel):client_ref:str;venue_id:int;actor_ref:str;shift_id:int|None=None;items:list[Item];payments:list[Payment];stock_cost:float=0;reward:int=0
@router.post("/finalize")
def finalize(p:Finalize,db:Session=Depends(dbd)):
 old=db.scalar(select(Tx).where(Tx.client_ref==p.client_ref))
 if old:return {"id":old.id,"status":old.status,"duplicate":True,"total":old.total,"paid":old.paid}
 if not p.items:raise HTTPException(400,"Sepet boş")
 total=round(sum((i.unit_price+sum(float(m.get("price_delta",0)) for m in i.modifiers))*i.qty for i in p.items),2);paid=round(sum(x.amount for x in p.payments),2)
 if any(x.amount<=0 for x in p.payments) or paid<total:raise HTTPException(409,"Ödeme tamamlanmadı")
 tx=Tx(client_ref=p.client_ref,venue_id=p.venue_id,shift_id=p.shift_id,actor_ref=p.actor_ref,total=total,paid=paid,stock_cost=p.stock_cost,reward=max(0,p.reward),payload=json.dumps(p.model_dump(),ensure_ascii=False));db.add(tx);db.flush()
 for typ,data in [("SALE_CREATED",{"total":total}),("PAYMENT_CAPTURED",{"paid":paid,"methods":[x.method for x in p.payments]}),("STOCK_CONSUMPTION_REQUESTED",{"items":[{"product_id":i.product_id,"qty":i.qty} for i in p.items]}),("REWARD_EARNED",{"reward":max(0,p.reward)}),("AUDIT_RECORDED",{"actor":p.actor_ref}),("ORDER_CLOSED",{"change":round(paid-total,2)})]:db.add(Event(transaction_id=tx.id,event_type=typ,payload=json.dumps(data,ensure_ascii=False)))
 db.commit();db.refresh(tx);return {"id":tx.id,"status":tx.status,"total":tx.total,"paid":tx.paid,"change":round(tx.paid-tx.total,2),"gross_margin":round(tx.total-tx.stock_cost,2),"reward":tx.reward}
@router.get("/{tid}")
def get(tid:int,db:Session=Depends(dbd)):
 tx=db.get(Tx,tid)
 if not tx:raise HTTPException(404,"İşlem bulunamadı")
 ev=db.scalars(select(Event).where(Event.transaction_id==tid).order_by(Event.id)).all();return {"id":tx.id,"client_ref":tx.client_ref,"status":tx.status,"total":tx.total,"paid":tx.paid,"events":[{"type":x.event_type,"payload":json.loads(x.payload)} for x in ev]}
