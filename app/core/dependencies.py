from dataclasses import dataclass
from datetime import datetime, timedelta
from typing import Annotated

from fastapi import Depends, Header, HTTPException
from jose import JWTError, jwt

from app.shared.config.business_config import business_config


@dataclass
class CurrentUser:
    user_id: str
    name: str = '调试用户'
    roles: tuple[str, ...] = ('knowledge_admin',)


def get_current_user(authorization: Annotated[str | None, Header()] = None) -> CurrentUser:
    if not authorization:
        return CurrentUser(user_id='debug-user')

    token = authorization.removeprefix('Bearer ').strip()
    try:
        payload = jwt.decode(token, business_config.jwt_secret, algorithms=[business_config.jwt_algorithm])
        return CurrentUser(
            user_id=str(payload.get('sub') or 'anonymous'),
            name=str(payload.get('name') or 'anonymous'),
            roles=tuple(payload.get('roles') or ['customer']),
        )
    except JWTError as exc:
        raise HTTPException(status_code=401, detail='Token 无效') from exc


def create_access_token(user_id: str, roles: list[str], expires_minutes: int | None = None) -> str:
    expire_at = datetime.utcnow() + timedelta(minutes=expires_minutes or business_config.jwt_expire_minutes)
    payload = {'sub': user_id, 'roles': roles, 'exp': expire_at}
    return jwt.encode(payload, business_config.jwt_secret, algorithm=business_config.jwt_algorithm)


def require_role(role: str):
    def _checker(user: CurrentUser = Depends(get_current_user)) -> CurrentUser:
        if role not in user.roles:
            raise HTTPException(status_code=403, detail='权限不足')
        return user

    return _checker
