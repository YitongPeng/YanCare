"""
员工排班模型
"""
from datetime import datetime, date
from sqlalchemy import String, Date, DateTime, ForeignKey, Boolean
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base


class Schedule(Base):
    """员工排班表"""
    __tablename__ = "schedules"
    
    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    
    # 关联
    staff_id: Mapped[int] = mapped_column(ForeignKey("users.id"), index=True)  # 员工ID
    store_id: Mapped[int] = mapped_column(ForeignKey("stores.id"), index=True)  # 门店ID
    
    # 排班日期
    work_date: Mapped[date] = mapped_column(Date, index=True)  # 工作日期
    
    # 工作时间段
    start_time: Mapped[str] = mapped_column(String(10))  # 开始时间，如 "09:00"
    end_time: Mapped[str] = mapped_column(String(10))    # 结束时间，如 "18:00"
    
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
    staff = relationship("User", back_populates="schedules")
    store = relationship("Store", back_populates="schedules")
