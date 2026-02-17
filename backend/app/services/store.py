"""
门店服务
"""
from typing import List, Optional
import math
import json
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.store import Store
from app.schemas.store import StoreCreate, StoreUpdate, StoreWithDistance


class StoreService:
    def __init__(self, db: AsyncSession):
        self.db = db
    
    async def get_stores(
        self, 
        latitude: Optional[float] = None, 
        longitude: Optional[float] = None
    ) -> List[StoreWithDistance]:
        """获取门店列表，可选按距离排序"""
        result = await self.db.execute(
            select(Store).where(Store.is_active == True)
        )
        stores = result.scalars().all()
        
        store_list = []
        for store in stores:
            store_data = StoreWithDistance(
                id=store.id,
                name=store.name,
                address=store.address,
                phone=store.phone,
                latitude=store.latitude,
                longitude=store.longitude,
                opening_time=store.opening_time,
                closing_time=store.closing_time,
                description=store.description,
                images=json.loads(store.images) if store.images else None,
                is_active=store.is_active,
                created_at=store.created_at,
                distance=None
            )
            
            # 计算距离
            if latitude and longitude and store.latitude and store.longitude:
                store_data.distance = self._calculate_distance(
                    latitude, longitude,
                    store.latitude, store.longitude
                )
            
            store_list.append(store_data)
        
        # 按距离排序
        if latitude and longitude:
            store_list.sort(key=lambda x: x.distance if x.distance else float('inf'))
        
        return store_list
    
    async def get_store(self, store_id: int) -> Optional[Store]:
        """获取门店详情"""
        result = await self.db.execute(
            select(Store).where(Store.id == store_id)
        )
        return result.scalar_one_or_none()
    
    async def create_store(self, store_data: StoreCreate) -> Store:
        """创建门店"""
        data = store_data.model_dump()
        if data.get('images'):
            data['images'] = json.dumps(data['images'])
        
        store = Store(**data)
        self.db.add(store)
        await self.db.flush()
        await self.db.refresh(store)
        return store
    
    async def update_store(self, store_id: int, store_data: StoreUpdate) -> Optional[Store]:
        """更新门店"""
        store = await self.get_store(store_id)
        if not store:
            return None
        
        update_data = store_data.model_dump(exclude_unset=True)
        if 'images' in update_data and update_data['images']:
            update_data['images'] = json.dumps(update_data['images'])
        
        for key, value in update_data.items():
            setattr(store, key, value)
        
        await self.db.flush()
        await self.db.refresh(store)
        return store
    
    def _calculate_distance(
        self, 
        lat1: float, lon1: float, 
        lat2: float, lon2: float
    ) -> float:
        """
        计算两点之间的距离（米）
        使用Haversine公式
        """
        R = 6371000  # 地球半径（米）
        
        lat1_rad = math.radians(lat1)
        lat2_rad = math.radians(lat2)
        delta_lat = math.radians(lat2 - lat1)
        delta_lon = math.radians(lon2 - lon1)
        
        a = (math.sin(delta_lat / 2) ** 2 + 
             math.cos(lat1_rad) * math.cos(lat2_rad) * 
             math.sin(delta_lon / 2) ** 2)
        c = 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))
        
        return R * c
