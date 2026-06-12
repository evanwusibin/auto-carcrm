from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api.routers import build_api_router
from app.core.exceptions import register_exception_handlers
from app.core.response import install_response_middleware
from app.shared.config.settings_config import settings
from app.core.lifespan import lifespan


def create_app() -> FastAPI:
    app = FastAPI(
        title='AutoCarCRM Backend',
        version='0.1.0',
        description='商用车售后诊断与报修知识助手后端服务',
        lifespan=lifespan,
    )

    app.add_middleware(
        CORSMiddleware,
        allow_origins=list(settings.cors_origins) or ['*'],
        allow_methods=['*'],
        allow_headers=['*'],
        allow_credentials=True,
    )

    install_response_middleware(app)
    register_exception_handlers(app)
    app.include_router(build_api_router())
    return app


app = create_app()
