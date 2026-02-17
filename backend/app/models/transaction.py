"""
消费记录模型 - 记录每次服务的扣卡次数
"""
from datetime import datetime
from typing import Optional
from sqlalchemy import Integer, DateTime, ForeignKey, Text, Enum as SQLEnum
from sqlalchemy.orm import Mapped, mapped_column, relationship
import enum

from app.database import Base
from app.models.card import ServiceType


class TransactionType(str, enum.Enum):
    """交易类型"""
    CONSUME = "consume"    # 消费（扣次）
    ADD = "add"            # 充值（加次）
    REFUND = "refund"      # 退款


class Transaction(Base):
    """消费记录表"""
    __tablename__ = "transactions"
    
    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    
    # 关联
    customer_id: Mapped[int] = mapped_column(ForeignKey("users.id"), index=True)  # 客户
    user_card_id: Mapped[int] = mapped_column(ForeignKey("user_cards.id"), index=True)  # 使用的卡
    appointment_id: Mapped[Optional[int]] = mapped_column(ForeignKey("appointments.id"), nullable=True)  # 关联预约
    
    # 交易信息
    transaction_type: Mapped[TransactionType] = mapped_column(SQLEnum(TransactionType))
    service_type: Mapped[ServiceType] = mapped_column(SQLEnum(ServiceType))
    times_changed: Mapped[int] = mapped_column(Integer)  # 变动次数（正数增加，负数减少）
    times_before: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)  # 变动前次数
    times_after: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)   # 变动后次数
    
    # 操作人
    operator_id: Mapped[int] = mapped_column(ForeignKey("users.id"))  # 操作员工
    
    # 备注
    notes: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    
    # 时间戳
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    
    # 关系
    customer = relationship("User", back_populates="transactions", foreign_keys=[customer_id])
    user_card = relationship("UserCard", back_populates="transactions")
    appointment = relationship("Appointment", back_populates="transaction")
