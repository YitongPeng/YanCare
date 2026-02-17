"""
门店相关的Schema
"""
from datetime import datetime
from typing import Optional, List
from pydantic import BaseModel


class StoreBase(BaseModel):
    """门店基础信息"""
    name: str
    address: str
    phone: Optional[str] = None
    latitude: Optional[float] = None
    longitude: Optional[float] = None
    opening_time: str = "09:00"
    closing_time: str = "21:00"
    description: Optional[str] = None


class StoreCreate(StoreBase):
    """创建门店"""
    images: Optional[List[str]] = None


class StoreUpdate(BaseModel):
    """更新门店"""
    name: Optional[str] = None
    address: Optional[str] = None
    phone: Optional[str] = None
    latitude: Optional[float] = None
    longitude: Optional[float] = None
    opening_time: Optional[str] = None
    closing_time: Optional[str] = None
    description: Optional[str] = None
    images: Optional[List[str]] = None
    is_active: Optional[bool] = None


class StoreResponse(StoreBase):
    """门店响应"""
    id: int
    images: Optional[List[str]] = None
    is_active: bool
    created_at: datetime
    
    class Config:
        from_attributes = True


class StoreWithDistance(StoreResponse):
    """带距离的门店信息"""
    distance: Optional[float] = None  # 距离（米）
