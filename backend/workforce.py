from __future__ import annotations
import os
from datetime import datetime,timezone
from fastapi import APIRouter,Depends,HTTPException
from pydantic import BaseModel
from sqlalchemy import DateTime,Integer,String,Text,create_engine,select
from sqlalchemy.orm import DeclarativeBase,Mapped,Session,mapped_column,sessionmaker
DB=os.getenv("DATABASE_URL","sqlite:///./faleora.db");e=create_engine(DB,future=True,connect_args={"check_same_thread":False} if DB.startswith("sqlite") else {});S=sessionmaker(bind=e,autoflush=False,expire_on_commit=False)
class B(DeclarativeBase):pass
class ShiftPlan(B):
 __tablename__="staff_shift_plans";id:Mapped[int]=mapped_column(primary_key=True);venue_id:Mapped[int]=mapped_column(Integer,index=True);staff_ref:Mapped[str]=mapped_column(String(120),index=True);role:Mapped[str]=mapped_column(String(60),index=True);zone:Mapped[str]=mapped_column(String(80),default="");starts_at:Mapped[datetime]=mapped_column(DateTime(timezone=True),index=True);ends_at:Mapped[datetime]=mapped_column(DateTime(timezone=True));status:Mapped[str]=mapped_column(String(20),default="planned")
class Handover(B):
 __tablename__="shift_handovers";id:Mapped[int]=mapped_column(primary_key=True);venue_id:Mapped[int]=mapped_column(Integer,index=True);from_staff:Mapped[str]=mapped_column(String(120));to_staff:Mapped[str]=mapped_column(String(120),default="");note:Mapped[str]=mapped_column(Text);created_at:Mapped[datetime]=mapped_column(DateTime(timezone=True),default=lambda:datetime.now(timezone.utc))
B.metadata.create_all(e);router=APIRouter(prefix="/api/workforce",tags=["workforce"])
def dbd():
 d=S()
 try:yield d
 finally:d.close()
class ShiftIn(BaseModel):venue_id:int;staff_ref:str;role:str;zone:str="";starts_at:datetime;ends_at:datetime
class HandoverIn(BaseModel):venue_id:int;from_staff:str;to_staff:str="";note:str
@router.post("/shifts")
def shift(p:ShiftIn,db:Session=Depends(dbd)):
 if p.ends_at<=p.starts_at:raise HTTPException(400,"Vardiya saatleri geçersiz")
 x=ShiftPlan(**p.model_dump());db.add(x);db.commit();db.refresh(x);return {"id":x.id}
@router.get("/venues/{venue_id}/shifts")
def shifts(venue_id:int,db:Session=Depends(dbd)):
 return [{"id":x.id,"staff_ref":x.staff_ref,"role":x.role,"zone":x.zone,"starts_at":x.starts_at,"ends_at":x.ends_at,"status":x.status} for x in db.scalars(select(ShiftPlan).where(ShiftPlan.venue_id==venue_id).order_by(ShiftPlan.starts_at)).all()]
@router.post("/handovers")
def handover(p:HandoverIn,db:Session=Depends(dbd)):
 x=Handover(**p.model_dump());db.add(x);db.commit();db.refresh(x);return {"id":x.id}
