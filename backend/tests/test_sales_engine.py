from fastapi import FastAPI
from fastapi.testclient import TestClient
from sales_engine import router
app=FastAPI();app.include_router(router);c=TestClient(app)
def test_sale_payment_lifecycle():
 p={"client_ref":"sale-test-1001","venue_id":999,"items":[{"product_id":1,"name":"Latte","qty":2,"unit_price":100,"modifiers":[{"name":"Ekstra","price_delta":10}]}]}
 a=c.post("/api/sales",json=p);assert a.status_code==200;sid=a.json()["id"];assert a.json()["total"]==220
 b=c.post(f"/api/sales/{sid}/send-kitchen");assert b.status_code==200
 q=c.post(f"/api/sales/{sid}/payments",json={"method":"cash","amount":100});assert q.json()["status"]!="closed"
 z=c.post(f"/api/sales/{sid}/payments",json={"method":"card","amount":120});assert z.json()["status"]=="closed" and z.json()["remaining"]==0
 d=c.post("/api/sales",json=p);assert d.json()["duplicate"] is True
