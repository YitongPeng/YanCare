"""
卡类型和用户持卡模型
"""
from datetime import datetime
from typing import Optional
from sqlalchemy import String, Integer, Float, Boolean, DateTime, ForeignKey, Text, Enum as SQLEnum
from sqlalchemy.orm import Mapped, mapped_column, relationship
import enum

from app.database import Base


class ServiceType(str, enum.Enum):
    """服务类型"""
    WASH = "wash"          # 洗头
    SOAK = "soak"          # 泡头
    CARE = "care"          # 养发
    COMBO = "combo"        # 综合（洗泡养）


class CardType(Base):
    """卡类型表 - 系统预设的卡种"""
    __tablename__ = "card_types"
    
    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    
    # 基本信息
    name: Mapped[str] = mapped_column(String(50))  # 卡名称
    service_type: Mapped[ServiceType] = mapped_column(SQLEnum(ServiceType))  # 服务类型
    
    # 卡属性
    total_times: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)  # 总次数，NULL表示无限次
    validity_days: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)  # 有效期天数，NULL表示永久
    
    # 价格（仅供展示/参考，不涉及支付）
    price: Mapped[float] = mapped_column(Float, default=0)
    single_price: Mapped[float] = mapped_column(Float, default=0)  # 单次价格
    
    # 使用规则
    deduct_times: Mapped[int] = mapped_column(Integer, default=1)  # 每次服务扣除次数
    duration_minutes: Mapped[int] = mapped_column(Integer, default=30)  # 服务时长（分钟）
    
    # 备注
    description: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    notes: Mapped[Optional[str]] = mapped_column(String(200), nullable=True)  # 注意事项
    
    # 状态
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    
    # 时间戳
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    
    # 关系
    user_cards = relationship("UserCard", back_populates="card_type")


class UserCard(Base):
    """用户持卡表 - 用户拥有的卡"""
    __tablename__ = "user_cards"
    
    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    
    # 关联
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id"), index=True)
    card_type_id: Mapped[int] = mapped_column(ForeignKey("card_types.id"))
    
    # 卡状态
    remaining_times: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)  # 剩余次数
    expire_date: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)  # 过期时间
    
    # 开卡信息
    created_by: Mapped[Optional[int]] = mapped_column(ForeignKey("users.id"), nullable=True)  # 开卡员工
    
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
    user = relationship("User", back_populates="cards", foreign_keys=[user_id])
    card_type = relationship("CardType", back_populates="user_cards")
    transactions = relationship("Transaction", back_populates="user_card")
