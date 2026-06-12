from datetime import datetime
from typing import Any

from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse


def success_response(data: Any = None, message: str = 'success', code: int = 0) -> dict[str, Any]:
    return {
        'code': code,
        'message': message,
        'data': data,
        'timestamp': datetime.now().isoformat(),
    }


def install_response_middleware(app: FastAPI) -> None:
    @app.middleware('http')
    async def add_process_time_header(request: Request, call_next):
        response = await call_next(request)
        response.headers['X-App-Name'] = 'auto-carcrm'
        return response


def json_error(message: str, code: int, status_code: int) -> JSONResponse:
    return JSONResponse(
        status_code=status_code,
        content={
            'code': code,
            'message': message,
            'data': None,
            'timestamp': datetime.now().isoformat(),
        },
    )
