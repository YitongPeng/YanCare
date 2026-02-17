"""
卡管理路由
"""
from typing import List
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.schemas.card import (
    CardTypeResponse, CardTypeCreate,
    UserCardResponse, UserCardCreate, UserCardSimple,
    NewCustomerCardCreate
)
from app.services.card import CardService
from app.services.auth import AuthService

router = APIRouter(prefix="/cards", tags=["卡管理"])


# ============ 卡类型 ============

@router.get("/types", response_model=List[CardTypeResponse])
async def get_card_types(
    db: AsyncSession = Depends(get_db)
):
    """获取所有卡类型"""
    card_service = CardService(db)
    return await card_service.get_card_types()


@router.post("/types", response_model=CardTypeResponse)
async def create_card_type(
    card_type_data: CardTypeCreate,
    db: AsyncSession = Depends(get_db),
    current_user = Depends(AuthService.require_admin)
):
    """创建卡类型（管理员）"""
    card_service = CardService(db)
    return await card_service.create_card_type(card_type_data)


# ============ 用户持卡 ============

@router.get("/my-cards", response_model=List[UserCardSimple])
async def get_my_cards(
    db: AsyncSession = Depends(get_db),
    current_user = Depends(AuthService.get_current_user)
):
    """获取我的卡列表（客户端）"""
    card_service = CardService(db)
    return await card_service.get_user_cards(current_user.id)


@router.get("/user/{user_id}", response_model=List[UserCardSimple])
async def get_user_cards(
    user_id: int,
    db: AsyncSession = Depends(get_db),
    current_user = Depends(AuthService.require_staff)
):
    """获取指定用户的卡列表（员工端）"""
    card_service = CardService(db)
    return await card_service.get_user_cards(user_id)


@router.post("/add-card", response_model=UserCardResponse)
async def add_card_to_user(
    card_data: UserCardCreate,
    db: AsyncSession = Depends(get_db),
    current_user = Depends(AuthService.require_staff)
):
    """
    给用户开卡（员工端）
    
    员工选择客户和卡类型，系统自动设置有效期和次数
    """
    card_service = CardService(db)
    return await card_service.add_card_to_user(
        user_id=card_data.user_id,
        card_type_id=card_data.card_type_id,
        created_by=current_user.id
    )


@router.post("/{user_card_id}/deduct")
async def deduct_card(
    user_card_id: int,
    times: int = 1,
    db: AsyncSession = Depends(get_db),
    current_user = Depends(AuthService.require_staff)
):
    """
    扣减卡次（核销时调用）
    """
    card_service = CardService(db)
    result = await card_service.deduct_card(
        user_card_id=user_card_id,
        times=times,
        operator_id=current_user.id
    )
    if not result:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="扣减失败，卡不存在或次数不足"
        )
    return {"success": True, "remaining_times": result}


@router.post("/new-customer-card", response_model=UserCardResponse)
async def create_new_customer_card(
    data: NewCustomerCardCreate,
    db: AsyncSession = Depends(get_db),
    current_user = Depends(AuthService.require_staff)
):
    """
    新客户开卡（员工端）
    
    1. 创建新客户（用手机号标识）
    2. 给客户开卡
    """
    card_service = CardService(db)
    return await card_service.create_new_customer_card(
        customer_name=data.customer_name,
        customer_phone=data.customer_phone,
        card_type_id=data.card_type_id,
        created_by=current_user.id
    )
