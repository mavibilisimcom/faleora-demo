from __future__ import annotations
import os,json
from datetime import datetime,timezone
from fastapi import APIRouter,Depends,HTTPException
from pydantic import BaseModel
from sqlalchemy import DateTime,Float,Integer,String,Text,UniqueConstraint,create_engine,select
from sqlalchemy.orm import DeclarativeBase,Mapped,Session,mapped_column,sessionmaker
DB=os.getenv("DATABASE_URL","sqlite:///./faleora.db");e=create_engine(DB,future=True,connect_args={"check_same_thread":False} if DB.startswith("sqlite") else {},pool_pre_ping=True);S=sessionmaker(bind=e,autoflush=False,expire_on_commit=False)
class B(DeclarativeBase):pass
class Sale(B):
 __tablename__="sale_transactions";__table_args__=(UniqueConstraint("client_ref",name="uq_sale_client_ref"),)
 id:Mapped[int]=mapped_column(primary_key=True);client_ref:Mapped[str]=mapped_column(String(120),index=True);venue_id:Mapped[int]=mapped_column(Integer,index=True);source:Mapped[str]=mapped_column(String(30),default="pos");status:Mapped[str]=mapped_column(String(30),default="open",index=True);total:Mapped[float]=mapped_column(Float,default=0);paid:Mapped[float]=mapped_column(Float,default=0);payload:Mapped[str]=mapped_column(Text,default="{}");created_at:Mapped[datetime]=mapped_column(DateTime(timezone=True),default=lambda:datetime.now(timezone.utc))
class SaleEvent(B):
 __tablename__="sale_events";id:Mapped[int]=mapped_column(primary_key=True);sale_id:Mapped[int]=mapped_column(Integer,index=True);event_type:Mapped[str]=mapped_column(String(50),index=True);payload:Mapped[str]=mapped_column(Text,default="{}");created_at:Mapped[datetime]=mapped_column(DateTime(timezone=True),default=lambda:datetime.now(timezone.utc))
B.metadata.create_all(e);router=APIRouter(prefix="/api/sales",tags=["sales"])
def dbd():
 d=S()
 try:yield d
 finally:d.close()
class Item(BaseModel):product_id:int;name:str;qty:int=1;unit_price:float;station:str="kitchen";modifiers:list[dict]=[]
class SaleIn(BaseModel):client_ref:str;venue_id:int;source:str="pos";items:list[Item]
class PayIn(BaseModel):method:str;amount:float;actor_ref:str="cashier"
@router.post("")
def create(p:SaleIn,db:Session=Depends(dbd)):
 old=db.scalar(select(Sale).where(Sale.client_ref==p.client_ref))
 if old:return {"id":old.id,"status":old.status,"duplicate":True,"total":old.total}
 if not p.items:raise HTTPException(400,"Sepet boş")
 total=sum((x.unit_price+sum(float(m.get("price_delta",0)) for m in x.modifiers))*x.qty for x in p.items)
 x=Sale(client_ref=p.client_ref,venue_id=p.venue_id,source=p.source,total=round(total,2),payload=json.dumps(p.model_dump(),ensure_ascii=False));db.add(x);db.flush();db.add(SaleEvent(sale_id=x.id,event_type="SALE_CREATED",payload=x.payload));db.commit();db.refresh(x);return {"id":x.id,"status":x.status,"total":x.total}
@router.post("/{sid}/send-kitchen")
def kitchen(sid:int,db:Session=Depends(dbd)):
 x=db.get(Sale,sid)
 if not x:raise HTTPException(404,"Satış bulunamadı")
 if x.status=="closed":raise HTTPException(409,"Adisyon kapalı")
 x.status="sent";db.add(SaleEvent(sale_id=x.id,event_type="ORDER_SENT_TO_KITCHEN"));db.commit();return {"ok":True,"status":x.status}
@router.post("/{sid}/payments")
def payment(sid:int,p:PayIn,db:Session=Depends(dbd)):
 x=db.get(Sale,sid)
 if not x:raise HTTPException(404,"Satış bulunamadı")
 if x.status=="closed":raise HTTPException(409,"Adisyon kapalı")
 if p.method not in {"cash","card","meal_card","online","other"} or p.amount<=0:raise HTTPException(400,"Ödeme geçersiz")
 x.paid=round(x.paid+p.amount,2);db.add(SaleEvent(sale_id=x.id,event_type="PAYMENT_CAPTURED",payload=json.dumps(p.model_dump(),ensure_ascii=False)))
 if x.paid>=x.total:
  x.status="closed";db.add(SaleEvent(sale_id=x.id,event_type="ORDER_CLOSED",payload=json.dumps({"change":round(x.paid-x.total,2)})))
 db.commit();return {"id":x.id,"paid":x.paid,"total":x.total,"remaining":max(0,round(x.total-x.paid,2)),"change":max(0,round(x.paid-x.total,2)),"status":x.status}
@router.get("/{sid}")
def get_sale(sid:int,db:Session=Depends(dbd)):
 x=db.get(Sale,sid)
 if not x:raise HTTPException(404,"Satış bulunamadı")
 ev=db.scalars(select(SaleEvent).where(SaleEvent.sale_id==sid).order_by(SaleEvent.id)).all();return {"id":x.id,"client_ref":x.client_ref,"venue_id":x.venue_id,"status":x.status,"total":x.total,"paid":x.paid,"events":[{"type":a.event_type,"created_at":a.created_at} for a in ev]}
