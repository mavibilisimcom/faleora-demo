from datetime import datetime,timezone
from fastapi import APIRouter
router=APIRouter(tags=['health'])
@router.get('/health')
def health():return {'status':'ok','service':'faleora-backend','time':datetime.now(timezone.utc).isoformat()}
@router.get('/ready')
def ready():return {'ready':True,'note':'process ready; external providers checked separately'}
