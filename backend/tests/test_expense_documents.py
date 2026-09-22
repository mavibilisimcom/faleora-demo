from fastapi import FastAPI
from fastapi.testclient import TestClient
from expense_documents import router
app=FastAPI();app.include_router(router);c=TestClient(app)
def test_document_requires_review_then_approval():
 a=c.post("/api/documents/drafts",json={"venue_id":993,"supplier":"Test","gross_amount":250,"tax_amount":25,"source":"photo","extracted":{"confidence":0.88}});assert a.status_code==200 and a.json()["status"]=="draft"
 b=c.post("/api/documents/"+str(a.json()["id"])+"/approve");assert b.status_code==200 and b.json()["status"]=="approved"
