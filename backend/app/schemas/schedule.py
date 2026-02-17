"""
排班相关的Schema
"""
from datetime import datetime, date
from typing import Optional, List
from pydantic import BaseModel

from app.schemas.user import StaffSimple
from app.schemas.store import StoreResponse


class ScheduleBase(BaseModel):
    """排班基础信息"""
    staff_id: int
    store_id: int
    work_date: date
    start_time: str
    end_time: str


class ScheduleCreate(ScheduleBase):
    """创建排班"""
    pass


class ScheduleBatchCreate(BaseModel):
    """批量创建排班"""
    store_id: int
    work_dates: List[date]  # 多个日期
    start_time: str
    end_time: str


class ScheduleUpdate(BaseModel):
    """更新排班"""
    store_id: Optional[int] = None
    start_time: Optional[str] = None
    end_time: Optional[str] = None
    is_active: Optional[bool] = None


class ScheduleResponse(ScheduleBase):
    """排班响应"""
    id: int
    is_active: bool
    created_at: datetime
    
    class Config:
        from_attributes = True


class ScheduleWithDetails(ScheduleResponse):
    """带详情的排班"""
    staff: StaffSimple
    store: StoreResponse


class AvailableStaff(BaseModel):
    """可预约的员工"""
    staff: StaffSimple
    available_times: List[str]  # 可用时间段列表，如 ["09:00", "09:30", "10:00"]
