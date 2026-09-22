from __future__ import annotations
import os
from fastapi import APIRouter,HTTPException
from pydantic import BaseModel
router=APIRouter(prefix="/api/e-documents",tags=["e-documents"])
class EDocIn(BaseModel):venue_id:int;document_type:str;reference:str;recipient_tax_id:str="";amount:float
@router.post("/prepare")
def prepare(p:EDocIn):
 if p.document_type not in {"e_arsiv","e_fatura","e_receipt"}:raise HTTPException(400,"Belge türü geçersiz")
 return {"status":"draft","provider":"not_configured","document":p.model_dump(),"message":"Yetkili e-belge entegratörü bağlandığında bu taslak sağlayıcıya gönderilecektir."}
