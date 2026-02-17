"""
预约服务
"""
from datetime import date, datetime
from typing import List, Optional
from sqlalchemy import select, and_, func
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.models.appointment import Appointment, AppointmentStatus
from app.models.card import CardType, ServiceType
from app.schemas.appointment import AppointmentCreate
from app.services.card import CardService


class AppointmentService:
    def __init__(self, db: AsyncSession):
        self.db = db
    
    async def create_appointment(
        self, 
        customer_id: int, 
        appointment_data: AppointmentCreate
    ) -> Optional[Appointment]:
        """创建预约"""
        # 获取服务时长
        duration = await self._get_service_duration(appointment_data.service_type)
        end_time = self._calculate_end_time(appointment_data.start_time, duration)
        
        # 检查时间段是否可用
        is_available = await self._check_time_available(
            staff_id=appointment_data.staff_id,
            appointment_date=appointment_data.appointment_date,
            start_time=appointment_data.start_time,
            end_time=end_time
        )
        
        if not is_available:
            return None
        
        # 创建预约
        appointment = Appointment(
            customer_id=customer_id,
            store_id=appointment_data.store_id,
            staff_id=appointment_data.staff_id,
            service_type=appointment_data.service_type,
            service_count=appointment_data.service_count,  # 服务数量（综合卡扣次用）
            appointment_date=appointment_data.appointment_date,
            start_time=appointment_data.start_time,
            end_time=end_time,
            notes=appointment_data.notes,
            status=AppointmentStatus.CONFIRMED  # 直接确认
        )
        self.db.add(appointment)
        await self.db.flush()
        await self.db.refresh(appointment)
        return appointment
    
    async def get_customer_appointments(
        self, 
        customer_id: int,
        status: Optional[AppointmentStatus] = None
    ) -> List[Appointment]:
        """获取客户的预约列表"""
        query = select(Appointment).options(
            selectinload(Appointment.staff),
            selectinload(Appointment.store)
        ).where(Appointment.customer_id == customer_id)
        
        if status:
            query = query.where(Appointment.status == status)
        
        query = query.order_by(Appointment.appointment_date.desc(), Appointment.start_time.desc())
        
        result = await self.db.execute(query)
        return result.scalars().all()
    
    async def get_staff_appointments(
        self,
        staff_id: int,
        appointment_date: Optional[date] = None,
        status: Optional[AppointmentStatus] = None
    ) -> List[Appointment]:
        """获取员工的预约列表"""
        query = select(Appointment).options(
            selectinload(Appointment.customer),
            selectinload(Appointment.store)
        ).where(Appointment.staff_id == staff_id)
        
        if appointment_date:
            query = query.where(Appointment.appointment_date == appointment_date)
        if status:
            query = query.where(Appointment.status == status)
        
        query = query.order_by(Appointment.appointment_date, Appointment.start_time)
        
        result = await self.db.execute(query)
        return result.scalars().all()
    
    async def cancel_appointment(self, appointment_id: int, user_id: int) -> bool:
        """取消预约"""
        result = await self.db.execute(
            select(Appointment).where(
                Appointment.id == appointment_id,
                Appointment.customer_id == user_id,
                Appointment.status.in_([AppointmentStatus.PENDING, AppointmentStatus.CONFIRMED])
            )
        )
        appointment = result.scalar_one_or_none()
        
        if not appointment:
            return False
        
        appointment.status = AppointmentStatus.CANCELLED
        await self.db.flush()
        return True
    
    async def complete_appointment(
        self,
        appointment_id: int,
        user_card_id: int,
        operator_id: int,
        notes: Optional[str] = None
    ) -> bool:
        """
        完成预约（核销）
        
        同时扣减客户的卡次
        """
        result = await self.db.execute(
            select(Appointment).where(
                Appointment.id == appointment_id,
                Appointment.status == AppointmentStatus.CONFIRMED
            )
        )
        appointment = result.scalar_one_or_none()
        
        if not appointment:
            return False
        
        # 获取服务需要扣减的次数（综合卡根据预约时选择的服务数量扣次）
        deduct_times = appointment.service_count if appointment.service_count else 1
        
        # 扣减卡次
        card_service = CardService(self.db)
        remaining = await card_service.deduct_card(
            user_card_id=user_card_id,
            times=deduct_times,
            operator_id=operator_id,
            service_type=appointment.service_type,
            appointment_id=appointment_id,
            notes=notes
        )
        
        if remaining is None:
            return False
        
        # 更新预约状态
        appointment.status = AppointmentStatus.COMPLETED
        appointment.completed_at = datetime.utcnow()
        appointment.completed_by = operator_id
        
        await self.db.flush()
        return True
    
    async def get_staff_stats(
        self,
        staff_id: int,
        start_date: Optional[date] = None,
        end_date: Optional[date] = None
    ) -> dict:
        """
        获取员工业绩统计
        
        返回各服务类型的完成数量
        """
        query = select(
            Appointment.service_type,
            func.count(Appointment.id).label('count')
        ).where(
            Appointment.staff_id == staff_id,
            Appointment.status == AppointmentStatus.COMPLETED
        ).group_by(Appointment.service_type)
        
        if start_date:
            query = query.where(Appointment.appointment_date >= start_date)
        if end_date:
            query = query.where(Appointment.appointment_date <= end_date)
        
        result = await self.db.execute(query)
        rows = result.all()
        
        stats = {
            "wash": 0,  # 洗头
            "soak": 0,  # 泡头
            "care": 0,  # 养发
            "combo": 0, # 综合
            "total": 0
        }
        
        for row in rows:
            service_type, count = row
            stats[service_type.value] = count
            stats["total"] += count
        
        return stats
    
    async def _check_time_available(
        self,
        staff_id: int,
        appointment_date: date,
        start_time: str,
        end_time: str
    ) -> bool:
        """检查时间段是否可用"""
        # 查找是否有冲突的预约
        result = await self.db.execute(
            select(Appointment).where(
                Appointment.staff_id == staff_id,
                Appointment.appointment_date == appointment_date,
                Appointment.status.in_([AppointmentStatus.PENDING, AppointmentStatus.CONFIRMED]),
                # 时间段重叠检查
                Appointment.start_time < end_time,
                Appointment.end_time > start_time
            )
        )
        existing = result.scalar_one_or_none()
        return existing is None
    
    async def _get_service_duration(self, service_type: ServiceType) -> int:
        """获取服务时长（分钟）"""
        duration_map = {
            ServiceType.WASH: 30,
            ServiceType.SOAK: 50,
            ServiceType.CARE: 50,
            ServiceType.COMBO: 50,
        }
        return duration_map.get(service_type, 30)
    
    async def _get_deduct_times(self, service_type: ServiceType, user_card_id: int) -> int:
        """
        获取需要扣减的次数
        
        综合卡做泡头或养发扣2次，其他扣1次
        """
        # 查询用户卡的类型
        from app.models.card import UserCard
        result = await self.db.execute(
            select(UserCard).options(selectinload(UserCard.card_type)).where(UserCard.id == user_card_id)
        )
        user_card = result.scalar_one_or_none()
        
        if not user_card:
            return 1
        
        # 综合卡做泡头或养发扣2次
        if user_card.card_type.service_type == ServiceType.COMBO:
            if service_type in [ServiceType.SOAK, ServiceType.CARE]:
                return 2
        
        return 1
    
    def _calculate_end_time(self, start_time: str, duration: int) -> str:
        """计算结束时间"""
        hours, minutes = map(int, start_time.split(':'))
        total_minutes = hours * 60 + minutes + duration
        end_hours = total_minutes // 60
        end_minutes = total_minutes % 60
        return f"{end_hours:02d}:{end_minutes:02d}"
