"""
预约路由
"""
from datetime import date
from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.models.appointment import AppointmentStatus
from app.schemas.appointment import (
    AppointmentCreate, AppointmentUpdate, 
    AppointmentResponse, AppointmentDetail, AppointmentComplete
)
from app.services.appointment import AppointmentService
from app.services.auth import AuthService

router = APIRouter(prefix="/appointments", tags=["预约"])


# ============ 客户端接口 ============

@router.post("", response_model=AppointmentResponse)
async def create_appointment(
    appointment_data: AppointmentCreate,
    db: AsyncSession = Depends(get_db),
    current_user = Depends(AuthService.get_current_user)
):
    """
    创建预约（客户端）
    
    客户选择门店、日期、时间、员工后创建预约
    """
    appointment_service = AppointmentService(db)
    result = await appointment_service.create_appointment(
        customer_id=current_user.id,
        appointment_data=appointment_data
    )
    if not result:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="预约失败，该时段已被占用"
        )
    return result


@router.get("/my-appointments", response_model=List[AppointmentDetail])
async def get_my_appointments(
    status: Optional[AppointmentStatus] = Query(None),
    db: AsyncSession = Depends(get_db),
    current_user = Depends(AuthService.get_current_user)
):
    """获取我的预约列表（客户端）"""
    appointment_service = AppointmentService(db)
    return await appointment_service.get_customer_appointments(
        customer_id=current_user.id,
        status=status
    )


@router.post("/{appointment_id}/cancel")
async def cancel_appointment(
    appointment_id: int,
    db: AsyncSession = Depends(get_db),
    current_user = Depends(AuthService.get_current_user)
):
    """取消预约（客户端）"""
    appointment_service = AppointmentService(db)
    result = await appointment_service.cancel_appointment(
        appointment_id=appointment_id,
        user_id=current_user.id
    )
    if not result:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="取消失败"
        )
    return {"success": True}


# ============ 员工端接口 ============

@router.get("/staff-appointments", response_model=List[AppointmentDetail])
async def get_staff_appointments(
    appointment_date: Optional[date] = Query(None),
    status: Optional[AppointmentStatus] = Query(None),
    db: AsyncSession = Depends(get_db),
    current_user = Depends(AuthService.require_staff)
):
    """获取我的预约列表（员工端）"""
    appointment_service = AppointmentService(db)
    return await appointment_service.get_staff_appointments(
        staff_id=current_user.id,
        appointment_date=appointment_date,
        status=status
    )


@router.post("/{appointment_id}/complete")
async def complete_appointment(
    appointment_id: int,
    complete_data: AppointmentComplete,
    db: AsyncSession = Depends(get_db),
    current_user = Depends(AuthService.require_staff)
):
    """
    完成预约（核销）
    
    员工核销服务，同时扣减客户的卡次
    """
    appointment_service = AppointmentService(db)
    result = await appointment_service.complete_appointment(
        appointment_id=appointment_id,
        user_card_id=complete_data.user_card_id,
        operator_id=current_user.id,
        notes=complete_data.notes
    )
    if not result:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="核销失败"
        )
    return {"success": True, "message": "核销成功"}


# ============ 统计接口 ============

@router.get("/staff-stats")
async def get_staff_stats(
    start_date: Optional[date] = Query(None),
    end_date: Optional[date] = Query(None),
    db: AsyncSession = Depends(get_db),
    current_user = Depends(AuthService.require_staff)
):
    """
    获取员工业绩统计
    
    返回指定时间段内的洗头和做头数量
    """
    appointment_service = AppointmentService(db)
    return await appointment_service.get_staff_stats(
        staff_id=current_user.id,
        start_date=start_date,
        end_date=end_date
    )
