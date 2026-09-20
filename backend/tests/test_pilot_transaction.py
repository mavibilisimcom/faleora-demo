from fastapi import FastAPI
from fastapi.testclient import TestClient
from pilot_transaction import router
app=FastAPI();app.include_router(router);c=TestClient(app)
def test_atomic_pilot_transaction_and_duplicate_guard():
 p={"client_ref":"pilot-tx-001","venue_id":996,"actor_ref":"cashier-1","items":[{"product_id":1,"name":"Latte","qty":2,"unit_price":100,"modifiers":[{"name":"Ekstra","price_delta":10}]}],"payments":[{"method":"cash","amount":100},{"method":"card","amount":120}],"stock_cost":60,"reward":5}
 a=c.post("/api/pilot-transaction/finalize",json=p);assert a.status_code==200 and a.json()["total"]==220 and a.json()["gross_margin"]==160
 b=c.post("/api/pilot-transaction/finalize",json=p);assert b.status_code==200 and b.json()["duplicate"] is True
 detail=c.get("/api/pilot-transaction/"+str(a.json()["id"]));types=[x["type"] for x in detail.json()["events"]];assert "ORDER_CLOSED" in types and "STOCK_CONSUMPTION_REQUESTED" in types and "AUDIT_RECORDED" in types
def test_atomic_pilot_transaction_rejects_underpayment():
 p={"client_ref":"pilot-tx-under","venue_id":996,"actor_ref":"cashier","items":[{"product_id":1,"name":"X","qty":1,"unit_price":100}],"payments":[{"method":"cash","amount":90}]}
 assert c.post("/api/pilot-transaction/finalize",json=p).status_code==409
