"""业务配置。"""
from dataclasses import dataclass

from app.shared.config.common import env_int, env_list, env_str


@dataclass
class BusinessConfig:
    jwt_secret: str
    jwt_algorithm: str
    jwt_expire_minutes: int
    diagnosis_risk_high_keywords: tuple[str, ...]


business_config = BusinessConfig(
    jwt_secret=env_str('JWT_SECRET', 'please-change-me'),
    jwt_algorithm=env_str('JWT_ALGORITHM', 'HS256'),
    jwt_expire_minutes=env_int('JWT_EXPIRE_MINUTES', 1440),
    diagnosis_risk_high_keywords=tuple(env_list('DIAGNOSIS_RISK_HIGH_KEYWORDS')),
)
