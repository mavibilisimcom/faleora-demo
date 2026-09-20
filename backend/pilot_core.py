from __future__ import annotations
import os,json
from datetime import datetime,timezone
from fastapi import APIRouter,Depends,HTTPException
from pydantic import BaseModel
from sqlalchemy import DateTime,Float,Integer,String,Text,UniqueConstraint,create_engine,select
from sqlalchemy.orm import DeclarativeBase,Mapped,Session,mapped_column,sessionmaker
DB=os.getenv("DATABASE_URL","sqlite:///./faleora.db");e=create_engine(DB,future=True,connect_args={"check_same_thread":False} if DB.startswith("sqlite") else {},pool_pre_ping=True);S=sessionmaker(bind=e,autoflush=False,expire_on_commit=False)
class B(DeclarativeBase):pass
class Recipe(B):
 __tablename__="pilot_recipe_lines";id:Mapped[int]=mapped_column(primary_key=True);venue_id:Mapped[int]=mapped_column(Integer,index=True);product_id:Mapped[int]=mapped_column(Integer,index=True);stock_item_id:Mapped[int]=mapped_column(Integer,index=True);qty_per_unit:Mapped[float]=mapped_column(Float);unit_cost:Mapped[float]=mapped_column(Float,default=0)
class Consumption(B):
 __tablename__="pilot_stock_consumption";__table_args__=(UniqueConstraint("sale_ref","stock_item_id",name="uq_sale_stock_consume"),)
 id:Mapped[int]=mapped_column(primary_key=True);venue_id:Mapped[int]=mapped_column(Integer,index=True);sale_ref:Mapped[str]=mapped_column(String(120),index=True);stock_item_id:Mapped[int]=mapped_column(Integer,index=True);qty:Mapped[float]=mapped_column(Float);cost:Mapped[float]=mapped_column(Float);created_at:Mapped[datetime]=mapped_column(DateTime(timezone=True),default=lambda:datetime.now(timezone.utc))
class Audit(B):
 __tablename__="pilot_audit";id:Mapped[int]=mapped_column(primary_key=True);venue_id:Mapped[int]=mapped_column(Integer,index=True);actor_ref:Mapped[str]=mapped_column(String(120));action:Mapped[str]=mapped_column(String(80),index=True);entity_ref:Mapped[str]=mapped_column(String(120));details:Mapped[str]=mapped_column(Text,default="{}");created_at:Mapped[datetime]=mapped_column(DateTime(timezone=True),default=lambda:datetime.now(timezone.utc))
B.metadata.create_all(e);router=APIRouter(prefix="/api/pilot",tags=["pilot-core"])
def dbd():
 d=S()
 try:yield d
 finally:d.close()
class RecipeIn(BaseModel):venue_id:int;product_id:int;stock_item_id:int;qty_per_unit:float;unit_cost:float=0
class ConsumeItem(BaseModel):product_id:int;qty:int
class ConsumeIn(BaseModel):venue_id:int;sale_ref:str;items:list[ConsumeItem];actor_ref:str="system"
@router.post("/recipes")
def recipe(p:RecipeIn,db:Session=Depends(dbd)):
 x=Recipe(**p.model_dump());db.add(x);db.commit();db.refresh(x);return {"id":x.id}
@router.post("/consume")
def consume(p:ConsumeIn,db:Session=Depends(dbd)):
 created=[];cost=0.0
 for item in p.items:
  rows=db.scalars(select(Recipe).where(Recipe.venue_id==p.venue_id,Recipe.product_id==item.product_id)).all()
  for r in rows:
   q=round(r.qty_per_unit*item.qty,6);old=db.scalar(select(Consumption).where(Consumption.sale_ref==p.sale_ref,Consumption.stock_item_id==r.stock_item_id))
   if old:continue
   x=Consumption(venue_id=p.venue_id,sale_ref=p.sale_ref,stock_item_id=r.stock_item_id,qty=-q,cost=round(q*r.unit_cost,2));db.add(x);created.append({"stock_item_id":r.stock_item_id,"qty":-q});cost+=x.cost
 db.add(Audit(venue_id=p.venue_id,actor_ref=p.actor_ref,action="STOCK_CONSUMED",entity_ref=p.sale_ref,details=json.dumps({"movements":created},ensure_ascii=False)));db.commit();return {"sale_ref":p.sale_ref,"movements":created,"stock_cost":round(cost,2)}
@router.get("/audit/{venue_id}")
def audit(venue_id:int,db:Session=Depends(dbd)):
 rows=db.scalars(select(Audit).where(Audit.venue_id==venue_id).order_by(Audit.id.desc()).limit(100)).all();return [{"action":x.action,"entity_ref":x.entity_ref,"actor_ref":x.actor_ref,"created_at":x.created_at} for x in rows]
