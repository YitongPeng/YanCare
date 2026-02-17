"""
门店路由
"""
from typing import Optional, List
from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.schemas.store import StoreCreate, StoreUpdate, StoreResponse, StoreWithDistance
from app.services.store import StoreService
from app.services.auth import AuthService

router = APIRouter(prefix="/stores", tags=["门店"])


@router.get("", response_model=List[StoreWithDistance])
async def get_stores(
    latitude: Optional[float] = Query(None, description="用户纬度"),
    longitude: Optional[float] = Query(None, description="用户经度"),
    db: AsyncSession = Depends(get_db)
):
    """
    获取门店列表
    
    如果提供了经纬度，会计算距离并按距离排序
    """
    store_service = StoreService(db)
    return await store_service.get_stores(latitude, longitude)


@router.get("/{store_id}", response_model=StoreResponse)
async def get_store(
    store_id: int,
    db: AsyncSession = Depends(get_db)
):
    """获取门店详情"""
    store_service = StoreService(db)
    store = await store_service.get_store(store_id)
    if not store:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="门店不存在"
        )
    return store


@router.post("", response_model=StoreResponse)
async def create_store(
    store_data: StoreCreate,
    db: AsyncSession = Depends(get_db),
    current_user = Depends(AuthService.require_admin)
):
    """创建门店（管理员）"""
    store_service = StoreService(db)
    return await store_service.create_store(store_data)


@router.put("/{store_id}", response_model=StoreResponse)
async def update_store(
    store_id: int,
    store_data: StoreUpdate,
    db: AsyncSession = Depends(get_db),
    current_user = Depends(AuthService.require_admin)
):
    """更新门店（管理员）"""
    store_service = StoreService(db)
    store = await store_service.update_store(store_id, store_data)
    if not store:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="门店不存在"
        )
    return store
