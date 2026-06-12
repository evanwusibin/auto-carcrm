from fastapi import APIRouter

from app.api.routers.health import router as health_router
from app.api.routers.knowledge import router as knowledge_router
from app.api.routers.qa import router as qa_router
from app.api.routers.vehicle import router as vehicle_router
from app.api.routers.warranty import router as warranty_router
from app.api.routers.diagnosis import router as diagnosis_router
from app.api.routers.repair import router as repair_router


def build_api_router() -> APIRouter:
    router = APIRouter()
    router.include_router(health_router)
    router.include_router(knowledge_router, prefix='/api/v1')
    router.include_router(qa_router, prefix='/api/v1')
    router.include_router(vehicle_router, prefix='/api/v1')
    router.include_router(warranty_router, prefix='/api/v1')
    router.include_router(diagnosis_router, prefix='/api/v1')
    router.include_router(repair_router, prefix='/api/v1')
    return router
