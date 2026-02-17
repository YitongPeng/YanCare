"""
认证相关的Schema
"""
from typing import Optional
from pydantic import BaseModel, field_validator

from app.schemas.user import UserResponse


class WechatLoginRequest(BaseModel):
    """微信登录请求"""
    code: str  # 微信登录code
    role: str = "customer"  # 角色：customer 或 staff
    staff_password: Optional[str] = None  # 员工密码（选择员工时必填）
    nickname: Optional[str] = None  # 昵称（首次登录时可填）
    avatar_url: Optional[str] = None  # 头像URL（微信授权获取）


class NameLoginRequest(BaseModel):
    """名字登录请求（顾客用名字直接登录，员工用名字+密码登录）"""
    name: str  # 用户名字（作为唯一账号标识）
    role: str = "customer"  # 角色：customer 或 staff
    staff_password: Optional[str] = None  # 员工密码（选择员工时必填）

    @field_validator("name")
    @classmethod
    def name_must_not_be_empty(cls, v: str) -> str:
        v = v.strip()
        if not v:
            raise ValueError("名字不能为空")
        return v


class TokenResponse(BaseModel):
    """Token响应"""
    access_token: str
    token_type: str = "bearer"
    user: UserResponse


class TokenData(BaseModel):
    """Token数据"""
    user_id: Optional[int] = None
    openid: Optional[str] = None
