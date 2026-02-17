"""
用户服务
"""
from typing import List, Optional
from sqlalchemy import select, or_, update
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.user import User, UserRole
from app.models.card import UserCard
from app.schemas.user import UserUpdate


class UserService:
    def __init__(self, db: AsyncSession):
        self.db = db
    
    async def get_user(self, user_id: int) -> Optional[User]:
        """获取用户"""
        result = await self.db.execute(select(User).where(User.id == user_id))
        return result.scalar_one_or_none()
    
    async def update_user(self, user_id: int, user_data: UserUpdate) -> Optional[User]:
        """更新用户信息"""
        user = await self.get_user(user_id)
        if not user:
            return None
        
        update_data = user_data.model_dump(exclude_unset=True)
        for key, value in update_data.items():
            setattr(user, key, value)
        
        await self.db.flush()
        await self.db.refresh(user)
        return user
    
    async def get_staff_list(self) -> List[User]:
        """获取员工列表"""
        result = await self.db.execute(
            select(User).where(
                User.role.in_([UserRole.STAFF, UserRole.ADMIN]),
                User.is_active == True
            )
        )
        return result.scalars().all()
    
    async def get_staff_detail(self, staff_id: int) -> Optional[User]:
        """获取员工详情"""
        result = await self.db.execute(
            select(User).where(
                User.id == staff_id,
                User.role.in_([UserRole.STAFF, UserRole.ADMIN])
            )
        )
        return result.scalar_one_or_none()
    
    async def search_users(
        self, 
        phone: Optional[str] = None, 
        nickname: Optional[str] = None
    ) -> List[User]:
        """搜索用户"""
        query = select(User).where(User.is_active == True)
        
        conditions = []
        if phone:
            conditions.append(User.phone.contains(phone))
        if nickname:
            conditions.append(User.nickname.contains(nickname))
        
        if conditions:
            query = query.where(or_(*conditions))
        
        result = await self.db.execute(query.limit(20))
        return result.scalars().all()
    
    async def bind_phone(self, user_id: int, phone: str) -> dict:
        """
        绑定手机号
        
        如果手机号已被其他用户使用（员工开卡时创建），
        则将那个用户的卡转移到当前用户
        """
        # 获取当前用户
        current_user = await self.get_user(user_id)
        if not current_user:
            raise ValueError("用户不存在")
        
        # 检查当前用户是否已绑定手机号
        if current_user.phone:
            raise ValueError("您已绑定手机号")
        
        cards_merged = False
        
        # 查找是否有其他用户使用这个手机号（员工开卡时创建的）
        # 可能有多个，所以用 scalars().all()
        result = await self.db.execute(
            select(User).where(
                User.phone == phone,
                User.id != user_id
            )
        )
        existing_users = result.scalars().all()
        
        for existing_user in existing_users:
            # 将那个用户的卡转移到当前用户
            await self.db.execute(
                update(UserCard)
                .where(UserCard.user_id == existing_user.id)
                .values(user_id=user_id)
            )
            
            # 如果那个用户没有真实的微信登录（是员工创建的占位用户），可以禁用它
            if existing_user.openid.startswith('phone_'):
                existing_user.is_active = False
                existing_user.phone = None  # 清除手机号避免冲突
            
            cards_merged = True
        
        # 更新当前用户的手机号
        current_user.phone = phone
        await self.db.flush()
        await self.db.refresh(current_user)
        
        return {
            "user": current_user,
            "cards_merged": cards_merged
        }
