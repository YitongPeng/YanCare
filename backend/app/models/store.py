"""
门店模型
"""
from datetime import datetime
from typing import Optional
from sqlalchemy import String, Float, Boolean, DateTime, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base


class Store(Base):
    """门店表"""
    __tablename__ = "stores"
    
    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    
    # 基本信息
    name: Mapped[str] = mapped_column(String(100))  # 门店名称
    address: Mapped[str] = mapped_column(String(200))  # 详细地址
    phone: Mapped[Optional[str]] = mapped_column(String(20), nullable=True)  # 联系电话
    
    # 位置信息（用于距离计算）
    latitude: Mapped[Optional[float]] = mapped_column(Float, nullable=True)  # 纬度
    longitude: Mapped[Optional[float]] = mapped_column(Float, nullable=True)  # 经度
    
    # 营业时间
    opening_time: Mapped[str] = mapped_column(String(10), default="09:00")  # 开门时间
    closing_time: Mapped[str] = mapped_column(String(10), default="21:00")  # 关门时间
    
    # 介绍
    description: Mapped[Optional[str]] = mapped_column(Text, nullable=True)  # 门店介绍
    images: Mapped[Optional[str]] = mapped_column(Text, nullable=True)  # 图片URL列表，JSON格式
    
    # 状态
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    
    # 时间戳
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime, 
        default=datetime.utcnow, 
        onupdate=datetime.utcnow
    )
    
    # 关系
    schedules = relationship("Schedule", back_populates="store")
    appointments = relationship("Appointment", back_populates="store")
