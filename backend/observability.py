from __future__ import annotations
import time,uuid
from fastapi import Request
async def request_context_middleware(request:Request,call_next):
 rid=request.headers.get("x-request-id") or str(uuid.uuid4())
 start=time.perf_counter()
 try:
  response=await call_next(request)
 except Exception:
  raise
 response.headers["x-request-id"]=rid
 response.headers["x-response-time-ms"]=str(round((time.perf_counter()-start)*1000,2))
 return response
