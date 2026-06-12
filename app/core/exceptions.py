from fastapi import FastAPI, HTTPException, Request
from fastapi.exceptions import RequestValidationError

from app.core.response import json_error
from app.shared.runtime.logger import logger


def register_exception_handlers(app: FastAPI) -> None:
    @app.exception_handler(RequestValidationError)
    async def validation_exception_handler(request: Request, exc: RequestValidationError):
        return json_error('参数错误', 1001, 422)

    @app.exception_handler(HTTPException)
    async def http_exception_handler(request: Request, exc: HTTPException):
        return json_error(exc.detail if isinstance(exc.detail, str) else '请求失败', 1004, exc.status_code)

    @app.exception_handler(Exception)
    async def unhandled_exception_handler(request: Request, exc: Exception):
        logger.exception('未处理异常')
        return json_error('服务器内部错误', 5000, 500)
