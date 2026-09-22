from datetime import datetime,timezone
from fastapi import APIRouter
from staging_check import evaluate
router=APIRouter(tags=['health'])
@router.get('/health')
def health():return {'status':'ok','service':'faleora-backend','time':datetime.now(timezone.utc).isoformat()}
@router.get('/ready')
def ready():
 r=evaluate()
 return {'ready':r['ready'],'checks':r['checks'],'note':'Dış sağlayıcılar ayrıca doğrulanmalıdır.'}
