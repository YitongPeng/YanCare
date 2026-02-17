"""
预约相关的Schema
"""
from datetime import datetime, date
from typing import Optional
from pydantic import BaseModel

from app.models.card import ServiceType
from app.models.appointment import AppointmentStatus
from app.schemas.user import UserResponse, StaffSimple
from app.schemas.store import StoreResponse


class AppointmentBase(BaseModel):
    """预约基础信息"""
    store_id: int
    staff_id: int
    service_type: ServiceType
    appointment_date: date
    start_time: str
    notes: Optional[str] = None


class AppointmentCreate(AppointmentBase):
    """创建预约（客户端）"""
    user_card_id: Optional[int] = None  # 使用的卡ID
    service_count: int = 1  # 服务数量（综合卡可选多个服务）


class AppointmentUpdate(BaseModel):
    """更新预约"""
    status: Optional[AppointmentStatus] = None
    notes: Optional[str] = None


class AppointmentResponse(AppointmentBase):
    """预约响应"""
    id: int
    customer_id: int
    end_time: str
    status: AppointmentStatus
    service_count: int = 1
    completed_at: Optional[datetime] = None
    created_at: datetime
    
    class Config:
        from_attributes = True


class AppointmentDetail(AppointmentResponse):
    """预约详情"""
    customer: UserResponse
    staff: StaffSimple
    store: StoreResponse


class AppointmentComplete(BaseModel):
    """完成预约（核销）"""
    user_card_id: int  # 使用哪张卡
    notes: Optional[str] = None
