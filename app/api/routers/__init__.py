from fastapi import APIRouter

from app.api.routers.chat import router as chat_router
from app.api.routers.diagnosis import router as diagnosis_router
from app.api.routers.health import router as health_router
from app.api.routers.import_kb import router as import_kb_router
from app.api.routers.knowledge import router as knowledge_router
from app.api.routers.qa import router as qa_router
from app.api.routers.repair import router as repair_router
from app.api.routers.vehicle import router as vehicle_router
from app.api.routers.warranty import router as warranty_router


def build_api_router() -> APIRouter:
    router = APIRouter()
    # 基础健康检查不带前缀，方便 K8s / Nginx 直接探活
    router.include_router(health_router)
    # 业务接口统一走 /api/v1 前缀
    router.include_router(knowledge_router, prefix='/api/v1')
    router.include_router(import_kb_router, prefix='/api/v1')
    router.include_router(qa_router, prefix='/api/v1')
    router.include_router(chat_router, prefix='/api/v1')
    router.include_router(vehicle_router, prefix='/api/v1')
    router.include_router(warranty_router, prefix='/api/v1')
    router.include_router(diagnosis_router, prefix='/api/v1')
    router.include_router(repair_router, prefix='/api/v1')
    return router
