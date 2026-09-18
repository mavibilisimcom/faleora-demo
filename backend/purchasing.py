from __future__ import annotations
import os
from datetime import datetime,timezone
from fastapi import APIRouter,Depends,HTTPException
from pydantic import BaseModel
from sqlalchemy import DateTime,Float,Integer,String,Text,create_engine,select
from sqlalchemy.orm import DeclarativeBase,Mapped,Session,mapped_column,sessionmaker
DB=os.getenv("DATABASE_URL","sqlite:///./faleora.db");e=create_engine(DB,future=True,connect_args={"check_same_thread":False} if DB.startswith("sqlite") else {});S=sessionmaker(bind=e,autoflush=False,expire_on_commit=False)
class B(DeclarativeBase):pass
class Supplier(B):
 __tablename__="suppliers";id:Mapped[int]=mapped_column(primary_key=True);venue_id:Mapped[int]=mapped_column(Integer,index=True);name:Mapped[str]=mapped_column(String(180));contact:Mapped[str]=mapped_column(String(220),default="");active:Mapped[int]=mapped_column(Integer,default=1)
class PurchaseOrder(B):
 __tablename__="purchase_orders";id:Mapped[int]=mapped_column(primary_key=True);venue_id:Mapped[int]=mapped_column(Integer,index=True);supplier_id:Mapped[int]=mapped_column(Integer,index=True);status:Mapped[str]=mapped_column(String(30),default="draft",index=True);total:Mapped[float]=mapped_column(Float,default=0);notes:Mapped[str]=mapped_column(Text,default="");created_at:Mapped[datetime]=mapped_column(DateTime(timezone=True),default=lambda:datetime.now(timezone.utc))
class PurchaseLine(B):
 __tablename__="purchase_lines";id:Mapped[int]=mapped_column(primary_key=True);purchase_order_id:Mapped[int]=mapped_column(Integer,index=True);stock_item_id:Mapped[int]=mapped_column(Integer,index=True);qty:Mapped[float]=mapped_column(Float);unit_price:Mapped[float]=mapped_column(Float)
B.metadata.create_all(e);router=APIRouter(prefix="/api/purchasing",tags=["purchasing"])
def dbd():
 d=S()
 try:yield d
 finally:d.close()
class SupplierIn(BaseModel):venue_id:int;name:str;contact:str=""
class POIn(BaseModel):venue_id:int;supplier_id:int;notes:str=""
class LineIn(BaseModel):stock_item_id:int;qty:float;unit_price:float
@router.post("/suppliers")
def supplier(p:SupplierIn,db:Session=Depends(dbd)):
 x=Supplier(**p.model_dump());db.add(x);db.commit();db.refresh(x);return {"id":x.id}
@router.post("/orders")
def po(p:POIn,db:Session=Depends(dbd)):
 if not db.get(Supplier,p.supplier_id):raise HTTPException(404,"Tedarikçi bulunamadı")
 x=PurchaseOrder(**p.model_dump());db.add(x);db.commit();db.refresh(x);return {"id":x.id,"status":x.status}
@router.post("/orders/{oid}/lines")
def line(oid:int,p:LineIn,db:Session=Depends(dbd)):
 o=db.get(PurchaseOrder,oid)
 if not o:raise HTTPException(404,"Sipariş bulunamadı")
 x=PurchaseLine(purchase_order_id=oid,**p.model_dump());db.add(x);o.total+=p.qty*p.unit_price;db.commit();return {"ok":True,"total":o.total}
@router.post("/orders/{oid}/status/{status}")
def status(oid:int,status:str,db:Session=Depends(dbd)):
 if status not in {"draft","approved","ordered","received","cancelled"}:raise HTTPException(400,"Geçersiz durum")
 o=db.get(PurchaseOrder,oid)
 if not o:raise HTTPException(404,"Sipariş bulunamadı")
 o.status=status;db.commit();return {"ok":True}
