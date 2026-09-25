from __future__ import annotations
import os
from datetime import datetime,timezone
from fastapi import APIRouter,Depends,HTTPException
from pydantic import BaseModel
from sqlalchemy import DateTime,Float,Integer,String,Text,create_engine,select
from sqlalchemy.orm import DeclarativeBase,Mapped,Session,mapped_column,sessionmaker
DB=os.getenv("DATABASE_URL","sqlite:///./faleora.db");e=create_engine(DB,future=True,connect_args={"check_same_thread":False} if DB.startswith("sqlite") else {});S=sessionmaker(bind=e,autoflush=False,expire_on_commit=False)
class B(DeclarativeBase):pass
class Product(B):
 __tablename__="pos_products";id:Mapped[int]=mapped_column(primary_key=True);venue_id:Mapped[int]=mapped_column(Integer,index=True);name:Mapped[str]=mapped_column(String(160));category:Mapped[str]=mapped_column(String(80),index=True);price:Mapped[float]=mapped_column(Float);station:Mapped[str]=mapped_column(String(60),default="kitchen");active:Mapped[int]=mapped_column(Integer,default=1)
class Order(B):
 __tablename__="pos_orders";id:Mapped[int]=mapped_column(primary_key=True);venue_id:Mapped[int]=mapped_column(Integer,index=True);source:Mapped[str]=mapped_column(String(30),default="table");table_ref:Mapped[str]=mapped_column(String(80),default="");status:Mapped[str]=mapped_column(String(30),default="open",index=True);total:Mapped[float]=mapped_column(Float,default=0);created_at:Mapped[datetime]=mapped_column(DateTime(timezone=True),default=lambda:datetime.now(timezone.utc))
class OrderItem(B):
 __tablename__="pos_order_items";id:Mapped[int]=mapped_column(primary_key=True);order_id:Mapped[int]=mapped_column(Integer,index=True);product_id:Mapped[int]=mapped_column(Integer);name:Mapped[str]=mapped_column(String(160));qty:Mapped[int]=mapped_column(Integer,default=1);unit_price:Mapped[float]=mapped_column(Float);station:Mapped[str]=mapped_column(String(60));notes:Mapped[str]=mapped_column(Text,default="");state:Mapped[str]=mapped_column(String(30),default="new",index=True)
class StockItem(B):
 __tablename__="stock_items";id:Mapped[int]=mapped_column(primary_key=True);venue_id:Mapped[int]=mapped_column(Integer,index=True);name:Mapped[str]=mapped_column(String(160));unit:Mapped[str]=mapped_column(String(20));qty:Mapped[float]=mapped_column(Float,default=0);min_qty:Mapped[float]=mapped_column(Float,default=0);unit_cost:Mapped[float]=mapped_column(Float,default=0)
B.metadata.create_all(e);router=APIRouter(prefix="/api/pos",tags=["pos"])
def dbd():
 d=S()
 try:yield d
 finally:d.close()
class ProductIn(BaseModel):venue_id:int;name:str;category:str;price:float;station:str="kitchen"
class ProductUpdate(BaseModel):name:str|None=None;category:str|None=None;price:float|None=None;station:str|None=None;active:int|None=None
class Line(BaseModel):product_id:int;qty:int=1;notes:str=""
class OrderIn(BaseModel):venue_id:int;source:str="table";table_ref:str="";items:list[Line]
@router.post("/products")
def product(p:ProductIn,db:Session=Depends(dbd)):
 x=Product(**p.model_dump());db.add(x);db.commit();db.refresh(x);return {"id":x.id}
@router.get("/venues/{venue_id}/products")
def products(venue_id:int,db:Session=Depends(dbd)):
 return [{"id":x.id,"name":x.name,"category":x.category,"price":x.price,"station":x.station} for x in db.scalars(select(Product).where(Product.venue_id==venue_id,Product.active==1)).all()]
@router.post("/orders")
def order(p:OrderIn,db:Session=Depends(dbd)):
 o=Order(venue_id=p.venue_id,source=p.source,table_ref=p.table_ref);db.add(o);db.flush();total=0
 for line in p.items:
  pr=db.get(Product,line.product_id)
  if not pr or pr.venue_id!=p.venue_id:raise HTTPException(400,"Ürün bulunamadı")
  total+=pr.price*line.qty;db.add(OrderItem(order_id=o.id,product_id=pr.id,name=pr.name,qty=line.qty,unit_price=pr.price,station=pr.station,notes=line.notes))
 o.total=total;o.status="sent";db.commit();db.refresh(o);return {"id":o.id,"total":o.total,"status":o.status}
@router.get("/kds/{venue_id}/{station}")
def kds(venue_id:int,station:str,db:Session=Depends(dbd)):
 orders=db.scalars(select(Order).where(Order.venue_id==venue_id,Order.status!="closed")).all();ids=[o.id for o in orders]
 if not ids:return []
 rows=db.scalars(select(OrderItem).where(OrderItem.order_id.in_(ids),OrderItem.station==station,OrderItem.state.in_(["new","preparing","ready"]))).all()
 return [{"id":x.id,"order_id":x.order_id,"name":x.name,"qty":x.qty,"notes":x.notes,"state":x.state} for x in rows]
@router.post("/kds/items/{item_id}/{state}")
def state(item_id:int,state:str,db:Session=Depends(dbd)):
 if state not in {"new","preparing","ready","served"}:raise HTTPException(400,"Geçersiz durum")
 x=db.get(OrderItem,item_id)
 if not x:raise HTTPException(404,"Kalem bulunamadı")
 x.state=state;db.commit();return {"ok":True}

@router.patch("/products/{product_id}")
def update_product(product_id:int,p:ProductUpdate,db:Session=Depends(dbd)):
 x=db.get(Product,product_id)
 if not x:raise HTTPException(404,"Ürün bulunamadı")
 for k,v in p.model_dump(exclude_none=True).items():setattr(x,k,v)
 db.commit();return {"id":x.id,"name":x.name,"category":x.category,"price":x.price,"station":x.station,"active":x.active}
@router.post("/products/{product_id}/sold-out")
def sold_out(product_id:int,sold_out:bool=True,db:Session=Depends(dbd)):
 x=db.get(Product,product_id)
 if not x:raise HTTPException(404,"Ürün bulunamadı")
 x.active=0 if sold_out else 1;db.commit();return {"id":x.id,"sold_out":sold_out}
