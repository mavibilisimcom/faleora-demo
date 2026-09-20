from fastapi import FastAPI
from fastapi.testclient import TestClient
from cash_reconciliation import router
app=FastAPI();app.include_router(router);c=TestClient(app)
def test_cash_shift_reconciliation():
 a=c.post("/api/cash/shifts",json={"venue_id":997,"cashier_ref":"test-cashier","opening_cash":1000});assert a.status_code==200;sid=a.json()["id"]
 c.post(f"/api/cash/shifts/{sid}/events",json={"event_type":"cash_sale","amount":250,"reference":"sale-x"})
 z=c.post(f"/api/cash/shifts/{sid}/close",json={"counted_cash":1240});assert z.status_code==200 and z.json()["difference"]==-10
