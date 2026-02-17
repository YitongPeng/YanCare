"""
卡相关的Schema
"""
from datetime import datetime
from typing import Optional
from pydantic import BaseModel

from app.models.card import ServiceType


class CardTypeBase(BaseModel):
    """卡类型基础信息"""
    name: str
    service_type: ServiceType
    total_times: Optional[int] = None  # None表示无限次
    validity_days: Optional[int] = None  # None表示永久
    price: float = 0
    single_price: float = 0
    deduct_times: int = 1
    duration_minutes: int = 30
    description: Optional[str] = None
    notes: Optional[str] = None


class CardTypeCreate(CardTypeBase):
    """创建卡类型"""
    pass


class CardTypeResponse(CardTypeBase):
    """卡类型响应"""
    id: int
    is_active: bool
    created_at: datetime
    
    class Config:
        from_attributes = True


class UserCardBase(BaseModel):
    """用户持卡基础信息"""
    user_id: int
    card_type_id: int


class UserCardCreate(UserCardBase):
    """创建用户持卡（员工给客户加卡）"""
    pass


class UserCardResponse(BaseModel):
    """用户持卡响应"""
    id: int
    user_id: int
    card_type_id: int
    remaining_times: Optional[int] = None
    expire_date: Optional[datetime] = None
    is_active: bool
    created_at: datetime
    card_type: CardTypeResponse
    
    class Config:
        from_attributes = True


class UserCardSimple(BaseModel):
    """用户持卡简要信息"""
    id: int
    card_name: str
    service_type: ServiceType
    remaining_times: Optional[int] = None  # None表示无限次
    expire_date: Optional[datetime] = None
    is_active: bool
    is_expired: bool = False
    
    class Config:
        from_attributes = True


class NewCustomerCardCreate(BaseModel):
    """新客户开卡"""
    customer_name: str
    customer_phone: str  # 手机号用于绑定
    card_type_id: int
    services: Optional[list] = None  # 选择的服务类型列表
