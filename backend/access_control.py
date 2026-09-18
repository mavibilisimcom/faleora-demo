from __future__ import annotations
import os
from datetime import datetime,timezone
from fastapi import APIRouter,Depends,HTTPException,Header
from pydantic import BaseModel
from sqlalchemy import Boolean,DateTime,Integer,String,create_engine,select
from sqlalchemy.orm import DeclarativeBase,Mapped,Session,mapped_column,sessionmaker
DB=os.getenv("DATABASE_URL","sqlite:///./faleora.db");e=create_engine(DB,future=True,connect_args={"check_same_thread":False} if DB.startswith("sqlite") else {});S=sessionmaker(bind=e,autoflush=False,expire_on_commit=False)
class B(DeclarativeBase):pass
class Principal(B):
 __tablename__="principals";id:Mapped[int]=mapped_column(primary_key=True);external_ref:Mapped[str]=mapped_column(String(160),unique=True,index=True);role:Mapped[str]=mapped_column(String(40),index=True);venue_id:Mapped[int|None]=mapped_column(Integer,nullable=True,index=True);active:Mapped[bool]=mapped_column(Boolean,default=True);created_at:Mapped[datetime]=mapped_column(DateTime(timezone=True),default=lambda:datetime.now(timezone.utc))
B.metadata.create_all(e);router=APIRouter(prefix="/api/access",tags=["access"])
ROLES={"user","reader","venue_owner","venue_manager","cashier","waiter","kitchen","expo","stock","partner","admin","enterprise"}
PERMS={"venue_owner":{"*"},"venue_manager":{"pos","tables","kds","staff","stock","cash","reports"},"cashier":{"pos","cash"},"waiter":{"pos","tables"},"kitchen":{"kds"},"expo":{"expo","kds"},"stock":{"stock"},"admin":{"*"},"enterprise":{"reports","venues"}}
def dbd():
 d=S()
 try:yield d
 finally:d.close()
class PrincipalIn(BaseModel):external_ref:str;role:str;venue_id:int|None=None
@router.post("/principals")
def add(p:PrincipalIn,db:Session=Depends(dbd)):
 if p.role not in ROLES:raise HTTPException(400,"Geçersiz rol")
 x=db.scalar(select(Principal).where(Principal.external_ref==p.external_ref)) or Principal(external_ref=p.external_ref)
 x.role=p.role;x.venue_id=p.venue_id;x.active=True;db.add(x);db.commit();db.refresh(x);return {"id":x.id,"role":x.role}
@router.get("/check")
def check(permission:str,x_principal:str=Header(default=""),db:Session=Depends(dbd)):
 p=db.scalar(select(Principal).where(Principal.external_ref==x_principal,Principal.active.is_(True)))
 if not p:raise HTTPException(401,"Principal bulunamadı")
 allowed=PERMS.get(p.role,set());return {"allowed":"*" in allowed or permission in allowed,"role":p.role,"venue_id":p.venue_id}
