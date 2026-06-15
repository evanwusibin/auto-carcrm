# -*- coding: utf-8 -*-
"""用户注册登录路由"""
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field
from passlib.context import CryptContext
from datetime import datetime
import pymongo
from app.core.dependencies import create_access_token

router = APIRouter(prefix="/auth", tags=["认证"])

# 密码加密
pwd_context = CryptContext(schemes=["sha256_crypt"], deprecated="auto")

# MongoDB连接
MONGO_URL = "mongodb://127.0.0.1:27017"
MONGO_DB = "auto_carcrm"
client = pymongo.MongoClient(MONGO_URL)
db = client[MONGO_DB]
users_collection = db["users"]


class UserRegister(BaseModel):
    """注册请求"""
    username: str = Field(..., min_length=3, max_length=20, description="用户名")
    password: str = Field(..., min_length=6, max_length=50, description="密码")
    email: str = Field(None, description="邮箱（可选）")
    phone: str = Field(None, description="手机号（可选）")


class UserLogin(BaseModel):
    """登录请求"""
    username: str = Field(..., description="用户名")
    password: str = Field(..., description="密码")


class UserResponse(BaseModel):
    """用户响应"""
    id: str
    username: str
    email: str = None
    phone: str = None
    created_at: str


@router.post("/register", summary="用户注册")
async def register(user: UserRegister):
    """
    用户注册接口
    
    - username: 用户名（3-20字符）
    - password: 密码（6-50字符）
    - email: 邮箱（可选）
    - phone: 手机号（可选）
    """
    # 检查用户名是否已存在
    if users_collection.find_one({"username": user.username}):
        raise HTTPException(status_code=400, detail="用户名已存在")
    
    # 密码加密
    hashed_password = pwd_context.hash(user.password)
    
    # 构造用户数据
    user_data = {
        "username": user.username,
        "password": hashed_password,
        "email": user.email,
        "phone": user.phone,
        "created_at": datetime.now().isoformat(),
        "updated_at": datetime.now().isoformat(),
        "is_active": True
    }
    
    # 插入数据库
    result = users_collection.insert_one(user_data)
    
    return {
        "code": 200,
        "message": "注册成功",
        "data": {
            "id": str(result.inserted_id),
            "username": user.username,
            "email": user.email,
            "phone": user.phone
        }
    }


@router.post("/login", summary="用户登录")
async def login(user: UserLogin):
    """
    用户登录接口
    
    - username: 用户名
    - password: 密码
    """
    # 查找用户
    db_user = users_collection.find_one({"username": user.username})
    if not db_user:
        raise HTTPException(status_code=401, detail="用户名或密码错误")
    
    # 验证密码
    if not pwd_context.verify(user.password, db_user["password"]):
        raise HTTPException(status_code=401, detail="用户名或密码错误")
    
    # 检查用户是否激活
    if not db_user.get("is_active", True):
        raise HTTPException(status_code=403, detail="账号已被禁用")
    
    # 生成 JWT token
    user_id = str(db_user["_id"])
    roles = db_user.get("roles", ["customer"])
    token = create_access_token(user_id=user_id, roles=roles)
    
    return {
        "code": 200,
        "message": "登录成功",
        "data": {
            "id": user_id,
            "username": db_user["username"],
            "email": db_user.get("email"),
            "phone": db_user.get("phone"),
            "roles": roles,
            "token": token,
            "created_at": db_user.get("created_at")
        }
    }


@router.get("/users", summary="获取用户列表")
async def get_users():
    """获取所有用户列表（不含密码）"""
    users = []
    for user in users_collection.find({}, {"password": 0}):
        users.append({
            "id": str(user["_id"]),
            "username": user["username"],
            "email": user.get("email"),
            "phone": user.get("phone"),
            "created_at": user.get("created_at"),
            "is_active": user.get("is_active", True)
        })
    return {"code": 200, "data": users}
