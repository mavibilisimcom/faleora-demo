from __future__ import annotations
import os
from datetime import datetime,timezone
from fastapi import APIRouter,Depends,HTTPException
from pydantic import BaseModel
from sqlalchemy import Boolean,DateTime,Float,Integer,String,create_engine,select
from sqlalchemy.orm import DeclarativeBase,Mapped,Session,mapped_column,sessionmaker
DB=os.getenv("DATABASE_URL","sqlite:///./faleora.db");e=create_engine(DB,future=True,connect_args={"check_same_thread":False} if DB.startswith("sqlite") else {});S=sessionmaker(bind=e,autoflush=False,expire_on_commit=False)
class B(DeclarativeBase):pass
class ModifierGroup(B):
 __tablename__="modifier_groups";id:Mapped[int]=mapped_column(primary_key=True);venue_id:Mapped[int]=mapped_column(Integer,index=True);name:Mapped[str]=mapped_column(String(120));required:Mapped[bool]=mapped_column(Boolean,default=False);min_select:Mapped[int]=mapped_column(Integer,default=0);max_select:Mapped[int]=mapped_column(Integer,default=1)
class Modifier(B):
 __tablename__="modifiers";id:Mapped[int]=mapped_column(primary_key=True);group_id:Mapped[int]=mapped_column(Integer,index=True);name:Mapped[str]=mapped_column(String(120));price_delta:Mapped[float]=mapped_column(Float,default=0);active:Mapped[bool]=mapped_column(Boolean,default=True)
class RecipeVersion(B):
 __tablename__="recipe_versions";id:Mapped[int]=mapped_column(primary_key=True);venue_id:Mapped[int]=mapped_column(Integer,index=True);product_id:Mapped[int]=mapped_column(Integer,index=True);version:Mapped[int]=mapped_column(Integer);effective_from:Mapped[datetime]=mapped_column(DateTime(timezone=True),default=lambda:datetime.now(timezone.utc),index=True);active:Mapped[bool]=mapped_column(Boolean,default=True)
class RecipeLine(B):
 __tablename__="recipe_lines";id:Mapped[int]=mapped_column(primary_key=True);recipe_version_id:Mapped[int]=mapped_column(Integer,index=True);stock_item_id:Mapped[int]=mapped_column(Integer,index=True);qty:Mapped[float]=mapped_column(Float);unit:Mapped[str]=mapped_column(String(20))
B.metadata.create_all(e);router=APIRouter(prefix="/api/menu-engine",tags=["menu-engine"])
def dbd():
 d=S()
 try:yield d
 finally:d.close()
class GroupIn(BaseModel):venue_id:int;name:str;required:bool=False;min_select:int=0;max_select:int=1
class ModifierIn(BaseModel):group_id:int;name:str;price_delta:float=0
class RecipeIn(BaseModel):venue_id:int;product_id:int
class LineIn(BaseModel):stock_item_id:int;qty:float;unit:str
@router.post("/modifier-groups")
def group(p:GroupIn,db:Session=Depends(dbd)):
 if p.max_select<p.min_select:raise HTTPException(400,"Seçim sınırı hatalı")
 x=ModifierGroup(**p.model_dump());db.add(x);db.commit();db.refresh(x);return {"id":x.id}
@router.post("/modifiers")
def modifier(p:ModifierIn,db:Session=Depends(dbd)):
 if not db.get(ModifierGroup,p.group_id):raise HTTPException(404,"Grup bulunamadı")
 x=Modifier(**p.model_dump());db.add(x);db.commit();db.refresh(x);return {"id":x.id}
@router.post("/recipes")
def recipe(p:RecipeIn,db:Session=Depends(dbd)):
 rows=db.scalars(select(RecipeVersion).where(RecipeVersion.venue_id==p.venue_id,RecipeVersion.product_id==p.product_id)).all();v=max([x.version for x in rows],default=0)+1
 for x in rows:x.active=False
 x=RecipeVersion(**p.model_dump(),version=v);db.add(x);db.commit();db.refresh(x);return {"id":x.id,"version":v}
@router.post("/recipes/{rid}/lines")
def line(rid:int,p:LineIn,db:Session=Depends(dbd)):
 if not db.get(RecipeVersion,rid):raise HTTPException(404,"Reçete bulunamadı")
 x=RecipeLine(recipe_version_id=rid,**p.model_dump());db.add(x);db.commit();return {"ok":True}
