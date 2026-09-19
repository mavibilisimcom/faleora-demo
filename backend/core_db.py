import os
from sqlalchemy import create_engine
from sqlalchemy.orm import DeclarativeBase,sessionmaker
DATABASE_URL=os.getenv("DATABASE_URL","sqlite:///./faleora.db")
kwargs={"pool_pre_ping":True}
if DATABASE_URL.startswith("sqlite"):kwargs["connect_args"]={"check_same_thread":False}
engine=create_engine(DATABASE_URL,future=True,**kwargs)
SessionLocal=sessionmaker(bind=engine,autoflush=False,expire_on_commit=False)
class Base(DeclarativeBase):pass
def db_session():
 db=SessionLocal()
 try:yield db
 finally:db.close()
