from fastapi import FastAPI
from fastapi.testclient import TestClient
from offline_sync import router
app=FastAPI();app.include_router(router);client=TestClient(app)
def test_offline_event_is_idempotent():
 p={"client_event_id":"test-event-001","venue_id":999,"device_id":"pos-test","event_type":"sale","payload":{"total":100}}
 a=client.post("/api/sync/events",json=p);assert a.status_code==200
 b=client.post("/api/sync/events",json=p);assert b.status_code==200 and b.json()["status"]=="duplicate"
