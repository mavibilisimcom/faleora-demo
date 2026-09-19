from fastapi import FastAPI
from fastapi.testclient import TestClient
from checkout_orchestrator import router
app=FastAPI();app.include_router(router);client=TestClient(app)
def test_underpaid_checkout_is_rejected():
 r=client.post("/api/checkout/finalize",json={"venue_id":999,"order_id":990001,"order_total":100,"paid_total":99,"stock_cost":20})
 assert r.status_code==409
def test_checkout_closes_once():
 payload={"venue_id":999,"order_id":990002,"order_total":100,"paid_total":120,"stock_cost":35,"reward_amount":5}
 r=client.post("/api/checkout/finalize",json=payload);assert r.status_code in (200,409)
 if r.status_code==200:
  assert r.json()["change"]==20.0 and r.json()["gross_margin"]==65.0
  assert client.post("/api/checkout/finalize",json=payload).status_code==409
