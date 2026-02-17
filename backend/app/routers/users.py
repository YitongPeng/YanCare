"""
用户路由
"""
from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.ext.asyncio import AsyncSession
from pydantic import BaseModel

from app.database import get_db
from app.schemas.user import UserUpdate, UserResponse, StaffResponse, StaffSimple
from app.services.user import UserService
from app.services.auth import AuthService

router = APIRouter(prefix="/users", tags=["用户"])


class BindPhoneRequest(BaseModel):
    phone: str


@router.put("/me", response_model=UserResponse)
async def update_my_info(
    user_data: UserUpdate,
    db: AsyncSession = Depends(get_db),
    current_user = Depends(AuthService.get_current_user)
):
    """更新我的信息"""
    user_service = UserService(db)
    return await user_service.update_user(current_user.id, user_data)


@router.get("/staff", response_model=List[StaffSimple])
async def get_staff_list(
    db: AsyncSession = Depends(get_db)
):
    """获取员工列表（用于展示）"""
    user_service = UserService(db)
    return await user_service.get_staff_list()


@router.get("/staff/{staff_id}", response_model=StaffResponse)
async def get_staff_detail(
    staff_id: int,
    db: AsyncSession = Depends(get_db)
):
    """获取员工详情"""
    user_service = UserService(db)
    staff = await user_service.get_staff_detail(staff_id)
    if not staff:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="员工不存在"
        )
    return staff


@router.get("/search", response_model=List[UserResponse])
async def search_users(
    phone: Optional[str] = Query(None, description="手机号"),
    nickname: Optional[str] = Query(None, description="昵称"),
    db: AsyncSession = Depends(get_db),
    current_user = Depends(AuthService.require_staff)
):
    """搜索用户（员工端，用于给客户加卡时搜索）"""
    user_service = UserService(db)
    return await user_service.search_users(phone=phone, nickname=nickname)


@router.post("/bind-phone")
async def bind_phone(
    data: BindPhoneRequest,
    db: AsyncSession = Depends(get_db),
    current_user = Depends(AuthService.get_current_user)
):
    """
    绑定手机号（客户端）
    
    如果该手机号已被其他用户（员工开卡时创建）使用，
    则将那个用户的卡转移到当前用户
    """
    user_service = UserService(db)
    result = await user_service.bind_phone(current_user.id, data.phone)
    return result
