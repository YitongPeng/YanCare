"""
用户模型 - 包含客户和员工
"""
from datetime import datetime
from typing import Optional, List, TYPE_CHECKING
from sqlalchemy import String, Boolean, DateTime, Enum as SQLEnum
from sqlalchemy.orm import Mapped, mapped_column, relationship
import enum

from app.database import Base


class UserRole(str, enum.Enum):
    """用户角色"""
    CUSTOMER = "customer"  # 客户
    STAFF = "staff"        # 员工
    ADMIN = "admin"        # 管理员


class User(Base):
    """用户表"""
    __tablename__ = "users"
    
    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    
    # 微信相关
    openid: Mapped[str] = mapped_column(String(64), unique=True, index=True)
    union_id: Mapped[Optional[str]] = mapped_column(String(64), nullable=True)
    
    # 基本信息
    nickname: Mapped[Optional[str]] = mapped_column(String(50), nullable=True)
    phone: Mapped[Optional[str]] = mapped_column(String(20), nullable=True, index=True)
    avatar_url: Mapped[Optional[str]] = mapped_column(String(500), nullable=True)
    
    # 角色和状态
    role: Mapped[UserRole] = mapped_column(
        SQLEnum(UserRole), 
        default=UserRole.CUSTOMER
    )
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    
    # 员工特有字段
    real_name: Mapped[Optional[str]] = mapped_column(String(50), nullable=True)  # 真实姓名
    employee_no: Mapped[Optional[str]] = mapped_column(String(20), nullable=True)  # 工号
    introduction: Mapped[Optional[str]] = mapped_column(String(500), nullable=True)  # 员工介绍
    
    # 时间戳
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime, 
        default=datetime.utcnow, 
        onupdate=datetime.utcnow
    )
    
    # 关系
    cards = relationship("UserCard", back_populates="user", foreign_keys="UserCard.user_id")
    appointments = relationship("Appointment", back_populates="customer", foreign_keys="Appointment.customer_id")
    staff_appointments = relationship("Appointment", back_populates="staff", foreign_keys="Appointment.staff_id")
    schedules = relationship("Schedule", back_populates="staff")
    transactions = relationship("Transaction", back_populates="customer", foreign_keys="Transaction.customer_id")
