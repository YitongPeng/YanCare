"""
预约模型
"""
from datetime import datetime, date
from typing import Optional
from sqlalchemy import String, Date, DateTime, ForeignKey, Enum as SQLEnum, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship
import enum

from app.database import Base
from app.models.card import ServiceType


class AppointmentStatus(str, enum.Enum):
    """预约状态"""
    PENDING = "pending"        # 待确认
    CONFIRMED = "confirmed"    # 已确认
    COMPLETED = "completed"    # 已完成
    CANCELLED = "cancelled"    # 已取消


class Appointment(Base):
    """预约表"""
    __tablename__ = "appointments"
    
    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    
    # 关联
    customer_id: Mapped[int] = mapped_column(ForeignKey("users.id"), index=True)  # 客户
    staff_id: Mapped[int] = mapped_column(ForeignKey("users.id"), index=True)     # 服务员工
    store_id: Mapped[int] = mapped_column(ForeignKey("stores.id"), index=True)    # 门店
    
    # 预约信息
    service_type: Mapped[ServiceType] = mapped_column(SQLEnum(ServiceType))  # 服务类型
    service_count: Mapped[int] = mapped_column(default=1)  # 服务数量（综合卡可多选）
    appointment_date: Mapped[date] = mapped_column(Date, index=True)  # 预约日期
    start_time: Mapped[str] = mapped_column(String(10))  # 开始时间
    end_time: Mapped[str] = mapped_column(String(10))    # 结束时间
    
    # 状态
    status: Mapped[AppointmentStatus] = mapped_column(
        SQLEnum(AppointmentStatus), 
        default=AppointmentStatus.PENDING
    )
    
    # 备注
    notes: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    
    # 核销信息
    completed_at: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)
    completed_by: Mapped[Optional[int]] = mapped_column(ForeignKey("users.id"), nullable=True)
    
    # 时间戳
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime, 
        default=datetime.utcnow, 
        onupdate=datetime.utcnow
    )
    
    # 关系
    customer = relationship("User", back_populates="appointments", foreign_keys=[customer_id])
    staff = relationship("User", back_populates="staff_appointments", foreign_keys=[staff_id])
    store = relationship("Store", back_populates="appointments")
    transaction = relationship("Transaction", back_populates="appointment", uselist=False)
