from __future__ import annotations
import os
from datetime import date,datetime,timezone
from fastapi import APIRouter,Depends
from sqlalchemy import DateTime,Float,Integer,String,create_engine,select,func
from sqlalchemy.orm import DeclarativeBase,Mapped,Session,mapped_column,sessionmaker
DB=os.getenv("DATABASE_URL","sqlite:///./faleora.db");e=create_engine(DB,future=True,connect_args={"check_same_thread":False} if DB.startswith("sqlite") else {},pool_pre_ping=True);S=sessionmaker(bind=e,autoflush=False,expire_on_commit=False)
router=APIRouter(prefix="/api/day-end",tags=["day-end"])
def dbd():
 d=S()
 try:yield d
 finally:d.close()
@router.get("/{venue_id}")
def report(venue_id:int,db:Session=Depends(dbd)):
 from sales_engine import Sale,SaleEvent
 from cash_reconciliation import Shift
 from pilot_core import Consumption
 sales=db.scalars(select(Sale).where(Sale.venue_id==venue_id,Sale.status=="closed")).all()
 total=round(sum(x.total for x in sales),2);paid=round(sum(x.paid for x in sales),2)
 costs=db.scalars(select(Consumption).where(Consumption.venue_id==venue_id)).all();stock_cost=round(sum(x.cost for x in costs),2)
 shifts=db.scalars(select(Shift).where(Shift.venue_id==venue_id)).all();cash_diff=round(sum((x.counted_cash-x.expected_cash) for x in shifts if x.status=="closed" and x.counted_cash is not None),2)
 return {"venue_id":venue_id,"closed_sales":len(sales),"net_sales":total,"collected":paid,"stock_cost":stock_cost,"gross_margin":round(total-stock_cost,2),"cash_difference":cash_diff,"generated_at":datetime.now(timezone.utc)}
