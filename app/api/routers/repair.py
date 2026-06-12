from fastapi import APIRouter, Depends

from app.core.dependencies import CurrentUser, get_current_user
from app.core.response import success_response
from app.domain.repair_service import repair_service

router = APIRouter(prefix='/repair-orders', tags=['repair'])


@router.post('')
def create_order(payload: dict, user: CurrentUser = Depends(get_current_user)):
    return success_response(repair_service.create(payload, user_id=user.user_id), message='报修单骨架调用成功')


@router.get('/{order_id}')
def get_order(order_id: str, user: CurrentUser = Depends(get_current_user)):
    return success_response(repair_service.get(order_id, user_id=user.user_id), message='报修单详情骨架调用成功')
