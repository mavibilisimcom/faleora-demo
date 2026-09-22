import os
from sqlalchemy import create_engine,text
def test_postgres_contract_when_configured():
 url=os.getenv("DATABASE_URL","")
 if not url.startswith("postgresql"):return
 e=create_engine(url,pool_pre_ping=True)
 with e.begin() as c:
  assert c.execute(text("select 1")).scalar()==1
