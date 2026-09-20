from __future__ import annotations
import asyncio,json,os
from datetime import datetime,timezone
from fastapi import APIRouter,WebSocket,WebSocketDisconnect
router=APIRouter(tags=["realtime"])
class Hub:
 def __init__(self):self.rooms={}
 async def join(self,room,ws):await ws.accept();self.rooms.setdefault(room,set()).add(ws)
 def leave(self,room,ws):
  if room in self.rooms:self.rooms[room].discard(ws)
 async def send(self,room,data):
  dead=[]
  for ws in list(self.rooms.get(room,set())):
   try:await ws.send_json(data)
   except:dead.append(ws)
  for ws in dead:self.leave(room,ws)
hub=Hub()
@router.websocket("/ws/venue/{venue_id}")
async def venue_ws(ws:WebSocket,venue_id:int):
 room=f"venue:{venue_id}";await hub.join(room,ws)
 try:
  await ws.send_json({"type":"CONNECTED","venue_id":venue_id,"time":datetime.now(timezone.utc).isoformat()})
  while True:
   data=await ws.receive_json()
   typ=str(data.get("type","CLIENT_EVENT"))
   await hub.send(room,{"type":typ,"payload":data.get("payload",{}),"time":datetime.now(timezone.utc).isoformat()})
 except WebSocketDisconnect:hub.leave(room,ws)
