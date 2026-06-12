from fastapi import APIRouter, Depends

from app.core.dependencies import CurrentUser, get_current_user
from app.core.response import success_response

router = APIRouter(prefix='/vehicles', tags=['vehicle'])


@router.get('/{vehicle_id}')
def get_vehicle(vehicle_id: str, user: CurrentUser = Depends(get_current_user)):
    return success_response({'vehicle_id': vehicle_id, 'user_id': user.user_id}, message='车辆详情骨架接口')
