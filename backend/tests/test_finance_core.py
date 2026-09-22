from fastapi import FastAPI
from fastapi.testclient import TestClient
from finance_core import router
app=FastAPI();app.include_router(router);c=TestClient(app)
def test_finance_income_expense_summary():
 a=c.post("/api/finance/accounts",json={"venue_id":994,"name":"Pilot Kasa","account_type":"cash","opening_balance":100});assert a.status_code==200
 aid=a.json()["id"];c.post("/api/finance/entries",json={"venue_id":994,"entry_type":"income","amount":500,"tax_amount":50,"account_id":aid,"reference":"sale-1"})
 c.post("/api/finance/entries",json={"venue_id":994,"entry_type":"expense","amount":120,"tax_amount":20,"account_id":aid,"reference":"expense-1"})
 s=c.get("/api/finance/venues/994/summary").json();assert s["operating_result"]==380 and s["tax_total"]==70
