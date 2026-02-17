"""
认证服务
"""
from datetime import datetime, timedelta
from typing import Optional
import httpx
from jose import jwt, JWTError
from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.config import settings
from app.database import get_db
from app.models.user import User, UserRole


security = HTTPBearer()


class AuthService:
    def __init__(self, db: AsyncSession):
        self.db = db
    
    async def name_login(
        self,
        name: str,
        role: str = "customer",
        staff_password: Optional[str] = None
    ) -> Optional[dict]:
        """
        名字登录（无需微信授权）
        
        1. 用名字作为唯一标识
        2. 验证员工密码（如果选择员工角色）
        3. 查找或创建用户
        4. 生成JWT token
        """
        # 如果选择员工角色，验证密码
        if role == "staff":
            if staff_password != settings.STAFF_PASSWORD:
                return {"error": "员工密码错误"}
        
        # 用名字生成唯一的 openid（区分顾客和员工）
        prefix = "staff_" if role == "staff" else "customer_"
        openid = f"{prefix}{name}"
        
        # 查找或创建用户
        user = await self._get_or_create_user(openid, role, name, None)
        
        # 生成token
        token = self._create_access_token(user.id, user.openid)
        
        return {
            "access_token": token,
            "token_type": "bearer",
            "user": user
        }
    
    async def wechat_login(
        self, 
        code: str, 
        role: str = "customer",
        staff_password: Optional[str] = None,
        nickname: Optional[str] = None,
        avatar_url: Optional[str] = None
    ) -> Optional[dict]:
        """
        微信登录
        
        1. 用code换取openid
        2. 验证员工密码（如果选择员工角色）
        3. 查找或创建用户
        4. 生成JWT token
        """
        # 如果选择员工角色，验证密码
        if role == "staff":
            if staff_password != settings.STAFF_PASSWORD:
                return {"error": "员工密码错误"}
        
        # 调用微信API获取openid（开发环境下员工用姓名作为标识）
        openid = await self._get_openid_from_code(code, role, nickname)
        if not openid:
            return None
        
        # 查找或创建用户
        user = await self._get_or_create_user(openid, role, nickname, avatar_url)
        
        # 生成token
        token = self._create_access_token(user.id, user.openid)
        
        return {
            "access_token": token,
            "token_type": "bearer",
            "user": user
        }
    
    async def _get_openid_from_code(
        self, 
        code: str, 
        role: str = "customer",
        nickname: Optional[str] = None
    ) -> Optional[str]:
        """调用微信API获取openid"""
        # 开发环境：使用固定的openid（方便测试）
        if settings.DEBUG and not settings.WECHAT_APP_ID:
            # 用姓名作为唯一标识，这样同一个名字就是同一个账号
            if nickname:
                prefix = "dev_staff_" if role == "staff" else "dev_customer_"
                return f"{prefix}{nickname}"
            # 如果没有姓名，用code（每次可能不同）
            return f"dev_{role}_{code}"
        
        # 生产环境：调用微信API
        url = "https://api.weixin.qq.com/sns/jscode2session"
        params = {
            "appid": settings.WECHAT_APP_ID,
            "secret": settings.WECHAT_APP_SECRET,
            "js_code": code,
            "grant_type": "authorization_code"
        }
        
        async with httpx.AsyncClient() as client:
            response = await client.get(url, params=params)
            data = response.json()
            
            if "openid" in data:
                return data["openid"]
            return None
    
    async def _get_or_create_user(
        self, 
        openid: str, 
        role: str = "customer",
        nickname: Optional[str] = None,
        avatar_url: Optional[str] = None
    ) -> User:
        """查找或创建用户"""
        result = await self.db.execute(
            select(User).where(User.openid == openid)
        )
        user = result.scalar_one_or_none()
        
        if not user:
            # 新用户，根据选择的角色创建
            user_role = UserRole.STAFF if role == "staff" else UserRole.CUSTOMER
            user = User(
                openid=openid,
                role=user_role,
                nickname=nickname,
                real_name=nickname if role == "staff" else None,
                avatar_url=avatar_url
            )
            self.db.add(user)
            await self.db.flush()
            await self.db.refresh(user)
        else:
            # 已有用户，更新昵称和头像
            if nickname:
                user.nickname = nickname
            if avatar_url:
                user.avatar_url = avatar_url
            
            # 如果选择了员工角色且密码正确，升级为员工
            if role == "staff" and user.role == UserRole.CUSTOMER:
                user.role = UserRole.STAFF
                if nickname:
                    user.real_name = nickname
            
            await self.db.flush()
            await self.db.refresh(user)
        
        return user
    
    def _create_access_token(self, user_id: int, openid: str) -> str:
        """创建JWT token"""
        expire = datetime.utcnow() + timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
        to_encode = {
            "sub": str(user_id),
            "openid": openid,
            "exp": expire
        }
        return jwt.encode(to_encode, settings.SECRET_KEY, algorithm=settings.ALGORITHM)
    
    @staticmethod
    async def get_current_user(
        credentials: HTTPAuthorizationCredentials = Depends(security),
        db: AsyncSession = Depends(get_db)
    ) -> User:
        """获取当前用户（从token解析）"""
        token = credentials.credentials
        
        try:
            payload = jwt.decode(token, settings.SECRET_KEY, algorithms=[settings.ALGORITHM])
            user_id = int(payload.get("sub"))
        except (JWTError, ValueError):
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="无效的认证凭证"
            )
        
        result = await db.execute(select(User).where(User.id == user_id))
        user = result.scalar_one_or_none()
        
        if not user or not user.is_active:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="用户不存在或已禁用"
            )
        
        return user
    
    @staticmethod
    async def require_staff(
        current_user: User = Depends(get_current_user)
    ) -> User:
        """要求员工权限"""
        if current_user.role not in [UserRole.STAFF, UserRole.ADMIN]:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="需要员工权限"
            )
        return current_user
    
    @staticmethod
    async def require_admin(
        current_user: User = Depends(get_current_user)
    ) -> User:
        """要求管理员权限"""
        if current_user.role != UserRole.ADMIN:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="需要管理员权限"
            )
        return current_user


# 辅助函数（用于依赖注入）
async def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(security),
    db: AsyncSession = Depends(get_db)
) -> User:
    """获取当前用户（从token解析）"""
    token = credentials.credentials
    
    try:
        payload = jwt.decode(token, settings.SECRET_KEY, algorithms=[settings.ALGORITHM])
        user_id = int(payload.get("sub"))
    except (JWTError, ValueError):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="无效的认证凭证"
        )
    
    result = await db.execute(select(User).where(User.id == user_id))
    user = result.scalar_one_or_none()
    
    if not user or not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="用户不存在或已禁用"
        )
    
    return user


async def require_staff(
    current_user: User = Depends(get_current_user)
) -> User:
    """要求员工权限"""
    if current_user.role not in [UserRole.STAFF, UserRole.ADMIN]:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="需要员工权限"
        )
    return current_user


async def require_admin(
    current_user: User = Depends(get_current_user)
) -> User:
    """要求管理员权限"""
    if current_user.role != UserRole.ADMIN:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="需要管理员权限"
        )
    return current_user


# 绑定到类上，方便导入使用
AuthService.get_current_user = get_current_user
AuthService.require_staff = require_staff
AuthService.require_admin = require_admin
