"""
卡管理服务
"""
from datetime import datetime, timedelta
from typing import List, Optional
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.models.card import CardType, UserCard, ServiceType
from app.models.user import User, UserRole
from app.models.transaction import Transaction, TransactionType
from app.schemas.card import CardTypeCreate, UserCardSimple


class CardService:
    def __init__(self, db: AsyncSession):
        self.db = db
    
    # ============ 卡类型 ============
    
    async def get_card_types(self) -> List[CardType]:
        """获取所有卡类型"""
        result = await self.db.execute(
            select(CardType).where(CardType.is_active == True)
        )
        return result.scalars().all()
    
    async def create_card_type(self, card_type_data: CardTypeCreate) -> CardType:
        """创建卡类型"""
        card_type = CardType(**card_type_data.model_dump())
        self.db.add(card_type)
        await self.db.flush()
        await self.db.refresh(card_type)
        return card_type
    
    # ============ 用户持卡 ============
    
    async def get_user_cards(self, user_id: int) -> List[UserCardSimple]:
        """获取用户的卡列表"""
        result = await self.db.execute(
            select(UserCard)
            .options(selectinload(UserCard.card_type))
            .where(UserCard.user_id == user_id, UserCard.is_active == True)
        )
        user_cards = result.scalars().all()
        
        now = datetime.utcnow()
        card_list = []
        for uc in user_cards:
            is_expired = uc.expire_date and uc.expire_date < now
            card_list.append(UserCardSimple(
                id=uc.id,
                card_name=uc.card_type.name,
                service_type=uc.card_type.service_type,
                remaining_times=uc.remaining_times,
                expire_date=uc.expire_date,
                is_active=uc.is_active,
                is_expired=is_expired
            ))
        
        return card_list
    
    async def add_card_to_user(
        self, 
        user_id: int, 
        card_type_id: int, 
        created_by: int
    ) -> UserCard:
        """
        给用户开卡
        
        根据卡类型自动设置有效期和次数
        """
        # 获取卡类型
        result = await self.db.execute(
            select(CardType).where(CardType.id == card_type_id)
        )
        card_type = result.scalar_one_or_none()
        if not card_type:
            raise ValueError("卡类型不存在")
        
        # 计算有效期
        expire_date = None
        if card_type.validity_days:
            expire_date = datetime.utcnow() + timedelta(days=card_type.validity_days)
        
        # 创建用户持卡
        user_card = UserCard(
            user_id=user_id,
            card_type_id=card_type_id,
            remaining_times=card_type.total_times,  # None表示无限次
            expire_date=expire_date,
            created_by=created_by
        )
        self.db.add(user_card)
        await self.db.flush()
        
        # 加载关联的card_type
        await self.db.refresh(user_card, ["card_type"])
        
        return user_card
    
    async def deduct_card(
        self, 
        user_card_id: int, 
        times: int, 
        operator_id: int,
        service_type: Optional[ServiceType] = None,
        appointment_id: Optional[int] = None,
        notes: Optional[str] = None
    ) -> Optional[int]:
        """
        扣减卡次
        
        返回剩余次数，失败返回None
        """
        result = await self.db.execute(
            select(UserCard)
            .options(selectinload(UserCard.card_type))
            .where(UserCard.id == user_card_id)
        )
        user_card = result.scalar_one_or_none()
        
        if not user_card or not user_card.is_active:
            return None
        
        # 检查是否过期
        if user_card.expire_date and user_card.expire_date < datetime.utcnow():
            return None
        
        # 检查次数是否足够（无限次卡不检查）
        times_before = user_card.remaining_times
        if user_card.remaining_times is not None:
            if user_card.remaining_times < times:
                return None
            user_card.remaining_times -= times
        
        times_after = user_card.remaining_times
        
        # 记录交易
        transaction = Transaction(
            customer_id=user_card.user_id,
            user_card_id=user_card_id,
            appointment_id=appointment_id,
            transaction_type=TransactionType.CONSUME,
            service_type=service_type or user_card.card_type.service_type,
            times_changed=-times,
            times_before=times_before,
            times_after=times_after,
            operator_id=operator_id,
            notes=notes
        )
        self.db.add(transaction)
        
        await self.db.flush()
        
        return user_card.remaining_times
    
    async def create_new_customer_card(
        self,
        customer_name: str,
        customer_phone: str,
        card_type_id: int,
        created_by: int
    ) -> UserCard:
        """
        新客户开卡
        
        1. 用手机号查找或创建客户账号
        2. 给客户开卡
        """
        # 先通过手机号查找是否已有用户
        result = await self.db.execute(
            select(User).where(User.phone == customer_phone)
        )
        user = result.scalar_one_or_none()
        
        if user:
            # 已有用户，更新姓名
            if customer_name and not user.nickname:
                user.nickname = customer_name
                user.real_name = customer_name
                await self.db.flush()
        else:
            # 创建新用户（用手机号作为唯一标识）
            user = User(
                openid=f"phone_{customer_phone}",
                phone=customer_phone,
                nickname=customer_name,
                real_name=customer_name,
                role=UserRole.CUSTOMER
            )
            self.db.add(user)
            await self.db.flush()
            await self.db.refresh(user)
        
        # 开卡
        return await self.add_card_to_user(
            user_id=user.id,
            card_type_id=card_type_id,
            created_by=created_by
        )
