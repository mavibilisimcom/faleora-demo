import os
os.environ.setdefault("AUTH_SECRET","test-secret")
from fastapi import FastAPI
from fastapi.testclient import TestClient
from auth import router
app=FastAPI();app.include_router(router);client=TestClient(app)
def test_register_login_me_flow():
 email="pilot-user@example.test"
 r=client.post("/api/auth/register",json={"email":email,"password":"strong-pass-123","role":"user"})
 assert r.status_code in (200,409)
 r=client.post("/api/auth/login",json={"email":email,"password":"strong-pass-123"});assert r.status_code==200
 token=r.json()["access_token"]
 me=client.get("/api/auth/me",headers={"Authorization":"Bearer "+token});assert me.status_code==200 and me.json()["email"]==email
 out=client.post("/api/auth/logout",headers={"Authorization":"Bearer "+token});assert out.status_code==200
 denied=client.get("/api/auth/me",headers={"Authorization":"Bearer "+token});assert denied.status_code==401
