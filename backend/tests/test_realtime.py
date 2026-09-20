from fastapi import FastAPI
from fastapi.testclient import TestClient
from realtime import router
app=FastAPI();app.include_router(router);c=TestClient(app)
def test_realtime_room_echo():
 with c.websocket_connect("/ws/venue/995") as ws:
  assert ws.receive_json()["type"]=="CONNECTED"
  ws.send_json({"type":"ORDER_READY","payload":{"order_id":1}})
  x=ws.receive_json();assert x["type"]=="ORDER_READY" and x["payload"]["order_id"]==1
