from fastapi import APIRouter, Depends

from app.core.dependencies import CurrentUser, get_current_user
from app.core.response import success_response

router = APIRouter(prefix='/knowledge', tags=['knowledge'])


@router.get('/documents')
def list_documents(user: CurrentUser = Depends(get_current_user)):
    return success_response({'items': [], 'owner': user.user_id}, message='知识文档列表占位接口')


@router.post('/documents/upload')
def upload_documents(user: CurrentUser = Depends(get_current_user)):
    return success_response({'task_ids': []}, message='知识导入上传接口骨架已就绪')
