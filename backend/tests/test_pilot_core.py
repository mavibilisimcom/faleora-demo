from fastapi import FastAPI
from fastapi.testclient import TestClient
from pilot_core import router
app=FastAPI();app.include_router(router);c=TestClient(app)
def test_recipe_consumption_is_idempotent():
 c.post("/api/pilot/recipes",json={"venue_id":998,"product_id":7001,"stock_item_id":8001,"qty_per_unit":0.15,"unit_cost":200})
 p={"venue_id":998,"sale_ref":"consume-001","items":[{"product_id":7001,"qty":2}],"actor_ref":"cashier"}
 a=c.post("/api/pilot/consume",json=p);assert a.status_code==200 and a.json()["movements"][0]["qty"]==-0.3
 b=c.post("/api/pilot/consume",json=p);assert b.status_code==200 and b.json()["movements"]==[]
