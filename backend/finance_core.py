from __future__ import annotations
import os
from datetime import date,datetime,timezone
from fastapi import APIRouter,Depends,HTTPException
from pydantic import BaseModel
from sqlalchemy import Date,DateTime,Float,Integer,String,Text,create_engine,select
from sqlalchemy.orm import DeclarativeBase,Mapped,Session,mapped_column,sessionmaker
DB=os.getenv("DATABASE_URL","sqlite:///./faleora.db");e=create_engine(DB,future=True,connect_args={"check_same_thread":False} if DB.startswith("sqlite") else {},pool_pre_ping=True);S=sessionmaker(bind=e,autoflush=False,expire_on_commit=False)
class B(DeclarativeBase):pass
class Account(B):
 __tablename__="finance_accounts";id:Mapped[int]=mapped_column(primary_key=True);venue_id:Mapped[int]=mapped_column(Integer,index=True);name:Mapped[str]=mapped_column(String(160));account_type:Mapped[str]=mapped_column(String(30),index=True);balance:Mapped[float]=mapped_column(Float,default=0)
class Ledger(B):
 __tablename__="finance_ledger";id:Mapped[int]=mapped_column(primary_key=True);venue_id:Mapped[int]=mapped_column(Integer,index=True);entry_type:Mapped[str]=mapped_column(String(30),index=True);amount:Mapped[float]=mapped_column(Float);tax_amount:Mapped[float]=mapped_column(Float,default=0);account_id:Mapped[int|None]=mapped_column(Integer,nullable=True,index=True);counterparty:Mapped[str]=mapped_column(String(180),default="");reference:Mapped[str]=mapped_column(String(120),default="",index=True);category:Mapped[str]=mapped_column(String(80),default="");entry_date:Mapped[date]=mapped_column(Date,default=date.today,index=True);notes:Mapped[str]=mapped_column(Text,default="");created_at:Mapped[datetime]=mapped_column(DateTime(timezone=True),default=lambda:datetime.now(timezone.utc))
B.metadata.create_all(e);router=APIRouter(prefix="/api/finance",tags=["finance"])
def dbd():
 d=S()
 try:yield d
 finally:d.close()
class AccountIn(BaseModel):venue_id:int;name:str;account_type:str;opening_balance:float=0
class EntryIn(BaseModel):venue_id:int;entry_type:str;amount:float;tax_amount:float=0;account_id:int|None=None;counterparty:str="";reference:str="";category:str="";entry_date:date=date.today();notes:str=""
@router.post("/accounts")
def account(p:AccountIn,db:Session=Depends(dbd)):
 if p.account_type not in {"cash","bank","receivable","payable"}:raise HTTPException(400,"Hesap türü geçersiz")
 x=Account(venue_id=p.venue_id,name=p.name,account_type=p.account_type,balance=p.opening_balance);db.add(x);db.commit();db.refresh(x);return {"id":x.id}
@router.post("/entries")
def entry(p:EntryIn,db:Session=Depends(dbd)):
 if p.entry_type not in {"income","expense","collection","payment"} or p.amount<=0:raise HTTPException(400,"Finans hareketi geçersiz")
 x=Ledger(**p.model_dump());db.add(x)
 if p.account_id:
  a=db.get(Account,p.account_id)
  if not a or a.venue_id!=p.venue_id:raise HTTPException(400,"Hesap bulunamadı")
  a.balance=round(a.balance+(p.amount if p.entry_type in {"income","collection"} else -p.amount),2)
 db.commit();db.refresh(x);return {"id":x.id}
@router.get("/venues/{venue_id}/summary")
def summary(venue_id:int,db:Session=Depends(dbd)):
 rows=db.scalars(select(Ledger).where(Ledger.venue_id==venue_id)).all();income=sum(x.amount for x in rows if x.entry_type=="income");expense=sum(x.amount for x in rows if x.entry_type=="expense");tax=sum(x.tax_amount for x in rows);return {"income":round(income,2),"expense":round(expense,2),"operating_result":round(income-expense,2),"tax_total":round(tax,2),"entries":len(rows)}
