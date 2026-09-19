from __future__ import annotations
import hashlib,hmac,os,secrets
from datetime import datetime,timedelta,timezone
from fastapi import APIRouter,Depends,Header,HTTPException
from pydantic import BaseModel
from sqlalchemy import Boolean,DateTime,Integer,String,create_engine,select
from sqlalchemy.orm import DeclarativeBase,Mapped,Session,mapped_column,sessionmaker
DB=os.getenv("DATABASE_URL","sqlite:///./faleora.db");SECRET=os.getenv("AUTH_SECRET","change-me-in-staging")
e=create_engine(DB,future=True,connect_args={"check_same_thread":False} if DB.startswith("sqlite") else {},pool_pre_ping=True);S=sessionmaker(bind=e,autoflush=False,expire_on_commit=False)
class B(DeclarativeBase):pass
class Account(B):
 __tablename__="auth_accounts";id:Mapped[int]=mapped_column(primary_key=True);email:Mapped[str]=mapped_column(String(220),unique=True,index=True);password_hash:Mapped[str]=mapped_column(String(256));role:Mapped[str]=mapped_column(String(40),default="user",index=True);venue_id:Mapped[int|None]=mapped_column(Integer,nullable=True,index=True);active:Mapped[bool]=mapped_column(Boolean,default=True);created_at:Mapped[datetime]=mapped_column(DateTime(timezone=True),default=lambda:datetime.now(timezone.utc))
class SessionToken(B):
 __tablename__="auth_sessions";id:Mapped[int]=mapped_column(primary_key=True);account_id:Mapped[int]=mapped_column(Integer,index=True);token_hash:Mapped[str]=mapped_column(String(64),unique=True,index=True);expires_at:Mapped[datetime]=mapped_column(DateTime(timezone=True),index=True);revoked:Mapped[bool]=mapped_column(Boolean,default=False)
B.metadata.create_all(e);router=APIRouter(prefix="/api/auth",tags=["auth"])
def dbd():
 d=S()
 try:yield d
 finally:d.close()
def ph(p,s=None):
 s=s or secrets.token_hex(16);v=hashlib.pbkdf2_hmac("sha256",p.encode(),s.encode(),310000).hex();return s+"$"+v
def pv(p,h):
 try:s,v=h.split("$",1);return hmac.compare_digest(ph(p,s).split("$",1)[1],v)
 except:return False
def th(t):return hashlib.sha256((t+SECRET).encode()).hexdigest()
class Register(BaseModel):email:str;password:str;role:str="user";venue_id:int|None=None
class Login(BaseModel):email:str;password:str
@router.post("/register")
def register(p:Register,db:Session=Depends(dbd)):
 if len(p.password)<10:raise HTTPException(400,"Şifre en az 10 karakter olmalı")
 if db.scalar(select(Account).where(Account.email==p.email.lower())):raise HTTPException(409,"E-posta kayıtlı")
 if p.role not in {"user","venue_owner","venue_manager","cashier","waiter","kitchen","expo","stock"}:raise HTTPException(400,"Geçersiz rol")
 x=Account(email=p.email.lower(),password_hash=ph(p.password),role=p.role,venue_id=p.venue_id);db.add(x);db.commit();db.refresh(x);return {"id":x.id,"role":x.role}
@router.post("/login")
def login(p:Login,db:Session=Depends(dbd)):
 a=db.scalar(select(Account).where(Account.email==p.email.lower(),Account.active.is_(True)))
 if not a or not pv(p.password,a.password_hash):raise HTTPException(401,"E-posta veya şifre hatalı")
 raw=secrets.token_urlsafe(40);x=SessionToken(account_id=a.id,token_hash=th(raw),expires_at=datetime.now(timezone.utc)+timedelta(hours=12));db.add(x);db.commit();return {"access_token":raw,"token_type":"bearer","expires_in":43200,"role":a.role,"venue_id":a.venue_id}
def current(authorization:str=Header(default=""),db:Session=Depends(dbd)):
 if not authorization.startswith("Bearer "):raise HTTPException(401,"Oturum gerekli")
 raw=authorization[7:];s=db.scalar(select(SessionToken).where(SessionToken.token_hash==th(raw),SessionToken.revoked.is_(False)))
 now=datetime.now(timezone.utc)
 if not s or s.expires_at.replace(tzinfo=timezone.utc) <= now:raise HTTPException(401,"Oturum geçersiz")
 a=db.get(Account,s.account_id)
 if not a or not a.active:raise HTTPException(401,"Hesap pasif")
 return a
@router.get("/me")
def me(a:Account=Depends(current)):return {"id":a.id,"email":a.email,"role":a.role,"venue_id":a.venue_id}
@router.post("/logout")
def logout(authorization:str=Header(default=""),db:Session=Depends(dbd)):
 if authorization.startswith("Bearer "):
  s=db.scalar(select(SessionToken).where(SessionToken.token_hash==th(authorization[7:])))
  if s:s.revoked=True;db.commit()
 return {"ok":True}
