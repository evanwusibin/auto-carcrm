from fastapi import APIRouter, Depends

from app.core.dependencies import CurrentUser, get_current_user
from app.core.response import success_response
from app.domain.warranty_service import warranty_service

router = APIRouter(prefix='/warranty', tags=['warranty'])


@router.post('/precheck')
def precheck_warranty(payload: dict, user: CurrentUser = Depends(get_current_user)):
    return success_response(warranty_service.precheck(payload, user_id=user.user_id), message='质保预判骨架调用成功')
