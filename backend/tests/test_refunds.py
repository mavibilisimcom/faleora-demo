from fastapi import FastAPI
from fastapi.testclient import TestClient
from refunds import router
app=FastAPI();app.include_router(router);c=TestClient(app)
def test_refund_requires_manager_and_is_idempotent():
 p={"client_ref":"refund-001","venue_id":994,"sale_ref":"sale-1","amount":50,"reason":"Ürün iadesi","actor_ref":"cashier","manager_ref":"","items":[]}
 assert c.post("/api/refunds",json=p).status_code==403
 p["manager_ref"]="manager-1";a=c.post("/api/refunds",json=p);assert a.status_code==200 and a.json()["audit"] is True
 b=c.post("/api/refunds",json=p);assert b.json()["duplicate"] is True
