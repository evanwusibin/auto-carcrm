from fastapi import APIRouter, Depends

from app.core.dependencies import CurrentUser, get_current_user
from app.core.response import success_response
from app.domain.diagnosis_service import diagnosis_service

router = APIRouter(prefix='/diagnosis', tags=['diagnosis'])


@router.post('/run')
def run_diagnosis(payload: dict, user: CurrentUser = Depends(get_current_user)):
    return success_response(diagnosis_service.run(payload, user_id=user.user_id), message='诊断骨架调用成功')
