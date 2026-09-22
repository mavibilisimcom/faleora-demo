from __future__ import annotations
import json,os
from datetime import date,datetime,timezone
from fastapi import APIRouter,Depends,HTTPException
from pydantic import BaseModel
from sqlalchemy import Date,DateTime,Float,Integer,String,Text,create_engine,select
from sqlalchemy.orm import DeclarativeBase,Mapped,Session,mapped_column,sessionmaker
DB=os.getenv("DATABASE_URL","sqlite:///./faleora.db");e=create_engine(DB,future=True,connect_args={"check_same_thread":False} if DB.startswith("sqlite") else {},pool_pre_ping=True);S=sessionmaker(bind=e,autoflush=False,expire_on_commit=False)
class B(DeclarativeBase):pass
class Document(B):
 __tablename__="expense_documents";id:Mapped[int]=mapped_column(primary_key=True);venue_id:Mapped[int]=mapped_column(Integer,index=True);supplier:Mapped[str]=mapped_column(String(180),default="");document_no:Mapped[str]=mapped_column(String(120),default="");document_date:Mapped[date]=mapped_column(Date,default=date.today);gross_amount:Mapped[float]=mapped_column(Float,default=0);tax_amount:Mapped[float]=mapped_column(Float,default=0);category:Mapped[str]=mapped_column(String(80),default="");status:Mapped[str]=mapped_column(String(30),default="draft",index=True);source:Mapped[str]=mapped_column(String(30),default="manual");extracted:Mapped[str]=mapped_column(Text,default="{}");created_at:Mapped[datetime]=mapped_column(DateTime(timezone=True),default=lambda:datetime.now(timezone.utc))
B.metadata.create_all(e);router=APIRouter(prefix="/api/documents",tags=["expense-documents"])
def dbd():
 d=S()
 try:yield d
 finally:d.close()
class DraftIn(BaseModel):venue_id:int;supplier:str="";document_no:str="";document_date:date=date.today();gross_amount:float=0;tax_amount:float=0;category:str="";source:str="manual";extracted:dict={}
@router.post("/drafts")
def draft(p:DraftIn,db:Session=Depends(dbd)):
 x=Document(**{**p.model_dump(),"extracted":json.dumps(p.extracted,ensure_ascii=False)});db.add(x);db.commit();db.refresh(x);return {"id":x.id,"status":x.status}
@router.post("/{did}/approve")
def approve(did:int,db:Session=Depends(dbd)):
 x=db.get(Document,did)
 if not x:raise HTTPException(404,"Belge bulunamadı")
 if x.gross_amount<=0:raise HTTPException(409,"Tutar kontrol edilmeli")
 x.status="approved";db.commit();return {"id":x.id,"status":x.status}
