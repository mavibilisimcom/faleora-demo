from __future__ import annotations
import os,json
from datetime import datetime,timezone
from fastapi import APIRouter,Depends,HTTPException
from pydantic import BaseModel
from sqlalchemy import DateTime,Float,Integer,String,Text,UniqueConstraint,create_engine,select
from sqlalchemy.orm import DeclarativeBase,Mapped,Session,mapped_column,sessionmaker
DB=os.getenv("DATABASE_URL","sqlite:///./faleora.db");e=create_engine(DB,future=True,connect_args={"check_same_thread":False} if DB.startswith("sqlite") else {},pool_pre_ping=True);S=sessionmaker(bind=e,autoflush=False,expire_on_commit=False)
class B(DeclarativeBase):pass
class Refund(B):
 __tablename__="pos_refunds";__table_args__=(UniqueConstraint("client_ref",name="uq_refund_ref"),)
 id:Mapped[int]=mapped_column(primary_key=True);client_ref:Mapped[str]=mapped_column(String(120),index=True);venue_id:Mapped[int]=mapped_column(Integer,index=True);sale_ref:Mapped[str]=mapped_column(String(120),index=True);amount:Mapped[float]=mapped_column(Float);reason:Mapped[str]=mapped_column(String(220));actor_ref:Mapped[str]=mapped_column(String(120));manager_ref:Mapped[str]=mapped_column(String(120),default="");status:Mapped[str]=mapped_column(String(30),default="approved");payload:Mapped[str]=mapped_column(Text,default="{}");created_at:Mapped[datetime]=mapped_column(DateTime(timezone=True),default=lambda:datetime.now(timezone.utc))
B.metadata.create_all(e);router=APIRouter(prefix="/api/refunds",tags=["refunds"])
def dbd():
 d=S()
 try:yield d
 finally:d.close()
class RefundIn(BaseModel):client_ref:str;venue_id:int;sale_ref:str;amount:float;reason:str;actor_ref:str;manager_ref:str;items:list[dict]=[]
@router.post("")
def refund(p:RefundIn,db:Session=Depends(dbd)):
 old=db.scalar(select(Refund).where(Refund.client_ref==p.client_ref))
 if old:return {"id":old.id,"status":old.status,"duplicate":True}
 if p.amount<=0 or not p.reason.strip():raise HTTPException(400,"İade bilgileri eksik")
 if not p.manager_ref.strip():raise HTTPException(403,"Müdür onayı gerekli")
 x=Refund(**p.model_dump(exclude={"items"}),payload=json.dumps({"items":p.items},ensure_ascii=False));db.add(x);db.commit();db.refresh(x);return {"id":x.id,"status":x.status,"reverse_cash":p.amount,"reverse_stock_items":p.items,"audit":True}
