"""
排班路由
"""
from datetime import date
from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.schemas.schedule import (
    ScheduleCreate, ScheduleBatchCreate, ScheduleUpdate,
    ScheduleResponse, ScheduleWithDetails, AvailableStaff
)
from app.services.schedule import ScheduleService
from app.services.auth import AuthService

router = APIRouter(prefix="/schedules", tags=["排班"])


@router.get("/available-staff", response_model=List[AvailableStaff])
async def get_available_staff(
    store_id: int = Query(..., description="门店ID"),
    work_date: date = Query(..., description="日期"),
    service_duration: int = Query(30, description="服务时长（分钟）"),
    db: AsyncSession = Depends(get_db)
):
    """
    获取指定门店、日期的可预约员工
    
    这是客户预约时调用的接口
    返回每个员工的可用时间段
    """
    schedule_service = ScheduleService(db)
    return await schedule_service.get_available_staff(
        store_id=store_id,
        work_date=work_date,
        service_duration=service_duration
    )


@router.get("/my-schedules", response_model=List[ScheduleWithDetails])
async def get_my_schedules(
    start_date: Optional[date] = Query(None),
    end_date: Optional[date] = Query(None),
    db: AsyncSession = Depends(get_db),
    current_user = Depends(AuthService.require_staff)
):
    """获取我的排班（员工端，包含门店信息）"""
    schedule_service = ScheduleService(db)
    return await schedule_service.get_staff_schedules(
        staff_id=current_user.id,
        start_date=start_date,
        end_date=end_date,
        include_store=True
    )


@router.post("", response_model=ScheduleResponse)
async def create_schedule(
    schedule_data: ScheduleCreate,
    db: AsyncSession = Depends(get_db),
    current_user = Depends(AuthService.require_staff)
):
    """创建排班（员工上传自己的上班时间）"""
    # 只能给自己排班
    if schedule_data.staff_id != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="只能设置自己的排班"
        )
    schedule_service = ScheduleService(db)
    return await schedule_service.create_schedule(schedule_data)


@router.post("/batch", response_model=List[ScheduleResponse])
async def create_schedules_batch(
    batch_data: ScheduleBatchCreate,
    db: AsyncSession = Depends(get_db),
    current_user = Depends(AuthService.require_staff)
):
    """批量创建排班（一次设置多天）"""
    schedule_service = ScheduleService(db)
    return await schedule_service.create_schedules_batch(
        staff_id=current_user.id,
        batch_data=batch_data
    )


@router.delete("/{schedule_id}")
async def delete_schedule(
    schedule_id: int,
    db: AsyncSession = Depends(get_db),
    current_user = Depends(AuthService.require_staff)
):
    """删除排班"""
    schedule_service = ScheduleService(db)
    result = await schedule_service.delete_schedule(
        schedule_id=schedule_id,
        staff_id=current_user.id
    )
    if not result:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="排班不存在或无权限删除"
        )
    return {"success": True}
