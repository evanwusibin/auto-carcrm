import uuid

from fastapi import APIRouter, Depends

from app.core.dependencies import CurrentUser, get_current_user
from app.core.response import success_response

router = APIRouter(prefix='/qa', tags=['qa'])


@router.post('/ask')
def ask_question(payload: dict, user: CurrentUser = Depends(get_current_user)):
    session_id = payload.get('session_id') or str(uuid.uuid4())
    query = payload.get('query', '')
    return success_response(
        {
            'session_id': session_id,
            'question': query,
            'answer': 'QA 统一接口骨架已建立，后续接入现有 query graph。',
            'references': [],
        },
        message='问答骨架接口已就绪',
    )
