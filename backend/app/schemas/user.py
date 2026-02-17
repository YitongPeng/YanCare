"""
用户相关的Schema
"""
from datetime import datetime
from typing import Optional
from pydantic import BaseModel

from app.models.user import UserRole


class UserBase(BaseModel):
    """用户基础信息"""
    nickname: Optional[str] = None
    phone: Optional[str] = None
    avatar_url: Optional[str] = None


class UserCreate(UserBase):
    """创建用户"""
    openid: str


class UserUpdate(UserBase):
    """更新用户"""
    real_name: Optional[str] = None
    introduction: Optional[str] = None


class StaffCreate(UserBase):
    """创建员工"""
    openid: str
    real_name: str
    employee_no: Optional[str] = None
    introduction: Optional[str] = None


class UserResponse(UserBase):
    """用户响应"""
    id: int
    openid: str
    role: UserRole
    is_active: bool
    created_at: datetime
    
    class Config:
        from_attributes = True


class StaffResponse(UserResponse):
    """员工响应"""
    real_name: Optional[str] = None
    employee_no: Optional[str] = None
    introduction: Optional[str] = None


class StaffSimple(BaseModel):
    """员工简要信息（用于列表展示）"""
    id: int
    real_name: Optional[str] = None
    nickname: Optional[str] = None
    avatar_url: Optional[str] = None
    introduction: Optional[str] = None
    
    class Config:
        from_attributes = True
