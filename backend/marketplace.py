from __future__ import annotations
import os
from datetime import datetime, timezone
from typing import Optional
from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy import Boolean, DateTime, Integer, String, Text, create_engine, select
from sqlalchemy.orm import DeclarativeBase, Mapped, Session, mapped_column, sessionmaker
DATABASE_URL=os.getenv('DATABASE_URL','sqlite:///./faleora.db')
engine=create_engine(DATABASE_URL,future=True,connect_args={'check_same_thread':False} if DATABASE_URL.startswith('sqlite') else {})
SessionLocal=sessionmaker(bind=engine,autoflush=False,expire_on_commit=False)
class Base(DeclarativeBase): pass
class Reader(Base):
    __tablename__='readers';id:Mapped[int]=mapped_column(primary_key=True);name:Mapped[str]=mapped_column(String(120));specialties:Mapped[str]=mapped_column(Text,default='');verified:Mapped[bool]=mapped_column(Boolean,default=False);active:Mapped[bool]=mapped_column(Boolean,default=True);rating_x100:Mapped[int]=mapped_column(Integer,default=500)
class ReadingOrder(Base):
    __tablename__='reading_orders';id:Mapped[int]=mapped_column(primary_key=True);reader_id:Mapped[int]=mapped_column(Integer,index=True);user_ref:Mapped[str]=mapped_column(String(120),index=True);reading_type:Mapped[str]=mapped_column(String(40));topic:Mapped[str]=mapped_column(String(80));delivery:Mapped[str]=mapped_column(String(20),default='text');status:Mapped[str]=mapped_column(String(30),default='queued');created_at:Mapped[datetime]=mapped_column(DateTime(timezone=True),default=lambda:datetime.now(timezone.utc))
class RewardLedger(Base):
    __tablename__='reward_ledger';id:Mapped[int]=mapped_column(primary_key=True);user_ref:Mapped[str]=mapped_column(String(120),index=True);amount:Mapped[int]=mapped_column(Integer);reason:Mapped[str]=mapped_column(String(120));created_at:Mapped[datetime]=mapped_column(DateTime(timezone=True),default=lambda:datetime.now(timezone.utc))
class Circle(Base):
    __tablename__='circles';id:Mapped[int]=mapped_column(primary_key=True);name:Mapped[str]=mapped_column(String(120));circle_type:Mapped[str]=mapped_column(String(40));owner_ref:Mapped[str]=mapped_column(String(120),index=True);private:Mapped[bool]=mapped_column(Boolean,default=True);created_at:Mapped[datetime]=mapped_column(DateTime(timezone=True),default=lambda:datetime.now(timezone.utc))
Base.metadata.create_all(engine)
router=APIRouter(prefix='/api/marketplace',tags=['marketplace'])
def db_dep():
    db=SessionLocal()
    try: yield db
    finally: db.close()
class ReaderCreate(BaseModel): name:str;specialties:str='';verified:bool=False
class OrderCreate(BaseModel): reader_id:int;user_ref:str;reading_type:str='coffee';topic:str='general';delivery:str='text'
class RewardCreate(BaseModel): user_ref:str;amount:int;reason:str
class CircleCreate(BaseModel): name:str;circle_type:str;owner_ref:str;private:bool=True
@router.get('/readers')
def readers(db:Session=Depends(db_dep)):
    rows=db.scalars(select(Reader).where(Reader.active.is_(True))).all();return [{'id':x.id,'name':x.name,'specialties':x.specialties,'verified':x.verified,'rating':x.rating_x100/100} for x in rows]
@router.post('/readers')
def add_reader(p:ReaderCreate,db:Session=Depends(db_dep)):
    x=Reader(**p.model_dump());db.add(x);db.commit();db.refresh(x);return {'id':x.id}
@router.post('/orders')
def order(p:OrderCreate,db:Session=Depends(db_dep)):
    if not db.get(Reader,p.reader_id): raise HTTPException(404,'Yorumcu bulunamadı')
    x=ReadingOrder(**p.model_dump());db.add(x);db.commit();db.refresh(x);return {'id':x.id,'status':x.status}
@router.post('/rewards')
def reward(p:RewardCreate,db:Session=Depends(db_dep)):
    x=RewardLedger(**p.model_dump());db.add(x);db.commit();return {'ok':True}
@router.get('/rewards/{user_ref}')
def balance(user_ref:str,db:Session=Depends(db_dep)):
    rows=db.scalars(select(RewardLedger).where(RewardLedger.user_ref==user_ref)).all();return {'user_ref':user_ref,'balance':sum(x.amount for x in rows),'entries':len(rows)}
@router.post('/circles')
def circle(p:CircleCreate,db:Session=Depends(db_dep)):
    x=Circle(**p.model_dump());db.add(x);db.commit();db.refresh(x);return {'id':x.id}
