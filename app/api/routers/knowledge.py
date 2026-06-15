from fastapi import APIRouter, Depends

from app.core.dependencies import CurrentUser, get_current_user
from app.core.response import success_response
from app.infra.persistence.knowledge_repository import knowledge_repository

router = APIRouter(prefix='/knowledge', tags=['knowledge'])


@router.get('/documents')
def list_documents(user: CurrentUser = Depends(get_current_user)):
    items = knowledge_repository.find_all_serialized()
    return success_response({'items': items, 'owner': user.user_id}, message='知识文档列表查询成功')


@router.post('/documents/upload')
def upload_documents(user: CurrentUser = Depends(get_current_user)):
    return success_response({'task_ids': []}, message='知识导入上传接口骨架已就绪')
