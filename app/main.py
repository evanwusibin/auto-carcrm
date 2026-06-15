from pathlib import Path
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles

from app.api.routers import build_api_router
from app.core.exceptions import register_exception_handlers
from app.core.response import install_response_middleware
from app.shared.config.settings_config import settings
from app.core.lifespan import lifespan

# 项目根目录
PROJECT_ROOT = Path(__file__).parent.parent
FRONTEND_DIR = PROJECT_ROOT / "frontend"


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

    # 静态文件服务（必须在API路由之前注册）
    app.mount("/images", StaticFiles(directory=str(FRONTEND_DIR / "images")), name="images")

    # 前端页面路由
    @app.get("/")
    async def root():
        return FileResponse(str(FRONTEND_DIR / "login.html"))

    @app.get("/login.html")
    async def login_page():
        return FileResponse(str(FRONTEND_DIR / "login.html"))

    @app.get("/search.html")
    async def search_page():
        return FileResponse(str(FRONTEND_DIR / "search.html"))

    @app.get("/import.html")
    async def import_page():
        return FileResponse(str(FRONTEND_DIR / "import.html"))

    # API路由（放在最后）
    app.include_router(build_api_router())

    return app


app = create_app()


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        app,
        host=settings.app_host,
        port=settings.import_app_port,
        log_level="info",
    )
