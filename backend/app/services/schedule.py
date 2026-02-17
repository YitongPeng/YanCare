"""
排班服务
"""
from datetime import date, datetime, timedelta
from typing import List, Optional
from sqlalchemy import select, and_
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.models.schedule import Schedule
from app.models.appointment import Appointment, AppointmentStatus
from app.models.user import User
from app.schemas.schedule import ScheduleCreate, ScheduleBatchCreate, AvailableStaff
from app.schemas.user import StaffSimple


class ScheduleService:
    def __init__(self, db: AsyncSession):
        self.db = db
    
    async def get_available_staff(
        self, 
        store_id: int, 
        work_date: date,
        service_duration: int = 30
    ) -> List[AvailableStaff]:
        """
        获取指定门店、日期的可预约员工及其可用时间段
        
        逻辑：
        1. 查找该门店该天有排班的员工
        2. 计算每个员工的可用时间段（排除已有预约）
        """
        # 获取该门店该天的排班
        result = await self.db.execute(
            select(Schedule)
            .options(selectinload(Schedule.staff))
            .where(
                Schedule.store_id == store_id,
                Schedule.work_date == work_date,
                Schedule.is_active == True
            )
        )
        schedules = result.scalars().all()
        
        available_staff_list = []
        
        for schedule in schedules:
            # 获取该员工当天的已有预约
            appointments_result = await self.db.execute(
                select(Appointment).where(
                    Appointment.staff_id == schedule.staff_id,
                    Appointment.appointment_date == work_date,
                    Appointment.status.in_([AppointmentStatus.PENDING, AppointmentStatus.CONFIRMED])
                )
            )
            appointments = appointments_result.scalars().all()
            
            # 计算已占用的时间段
            occupied_times = set()
            for apt in appointments:
                # 将预约时间段内的所有时间点标记为已占用
                start = self._time_to_minutes(apt.start_time)
                end = self._time_to_minutes(apt.end_time)
                for t in range(start, end, 30):  # 以30分钟为单位
                    occupied_times.add(t)
            
            # 计算可用时间段
            available_times = []
            start_minutes = self._time_to_minutes(schedule.start_time)
            end_minutes = self._time_to_minutes(schedule.end_time)
            
            current = start_minutes
            while current + service_duration <= end_minutes:
                # 检查这个时间段是否可用
                is_available = True
                for t in range(current, current + service_duration, 30):
                    if t in occupied_times:
                        is_available = False
                        break
                
                if is_available:
                    available_times.append(self._minutes_to_time(current))
                
                current += 30  # 每30分钟一个时间点
            
            if available_times:
                staff_simple = StaffSimple(
                    id=schedule.staff.id,
                    real_name=schedule.staff.real_name,
                    nickname=schedule.staff.nickname,
                    avatar_url=schedule.staff.avatar_url,
                    introduction=schedule.staff.introduction
                )
                available_staff_list.append(AvailableStaff(
                    staff=staff_simple,
                    available_times=available_times
                ))
        
        return available_staff_list
    
    async def get_staff_schedules(
        self, 
        staff_id: int,
        start_date: Optional[date] = None,
        end_date: Optional[date] = None,
        include_store: bool = False
    ) -> List[Schedule]:
        """获取员工的排班"""
        query = select(Schedule).where(
            Schedule.staff_id == staff_id,
            Schedule.is_active == True
        )
        
        # 加载门店和员工信息
        if include_store:
            query = query.options(
                selectinload(Schedule.store),
                selectinload(Schedule.staff)
            )
        
        if start_date:
            query = query.where(Schedule.work_date >= start_date)
        if end_date:
            query = query.where(Schedule.work_date <= end_date)
        
        result = await self.db.execute(query.order_by(Schedule.work_date))
        return result.scalars().all()
    
    async def create_schedule(self, schedule_data: ScheduleCreate) -> Schedule:
        """创建排班"""
        # 检查是否已有排班
        existing_result = await self.db.execute(
            select(Schedule).where(
                Schedule.staff_id == schedule_data.staff_id,
                Schedule.work_date == schedule_data.work_date,
                Schedule.is_active == True
            )
        )
        schedule = existing_result.scalar_one_or_none()
        if schedule:
            # 更新现有排班
            schedule.store_id = schedule_data.store_id
            schedule.start_time = schedule_data.start_time
            schedule.end_time = schedule_data.end_time
        else:
            schedule = Schedule(**schedule_data.model_dump())
            self.db.add(schedule)
        
        await self.db.flush()
        await self.db.refresh(schedule)
        return schedule
    
    async def create_schedules_batch(
        self, 
        staff_id: int,
        batch_data: ScheduleBatchCreate
    ) -> List[Schedule]:
        """批量创建排班"""
        schedules = []
        for work_date in batch_data.work_dates:
            schedule_data = ScheduleCreate(
                staff_id=staff_id,
                store_id=batch_data.store_id,
                work_date=work_date,
                start_time=batch_data.start_time,
                end_time=batch_data.end_time
            )
            schedule = await self.create_schedule(schedule_data)
            schedules.append(schedule)
        return schedules
    
    async def delete_schedule(self, schedule_id: int, staff_id: int) -> bool:
        """删除排班"""
        result = await self.db.execute(
            select(Schedule).where(
                Schedule.id == schedule_id,
                Schedule.staff_id == staff_id
            )
        )
        schedule = result.scalar_one_or_none()
        
        if not schedule:
            return False
        
        schedule.is_active = False
        await self.db.flush()
        return True
    
    def _time_to_minutes(self, time_str: str) -> int:
        """将时间字符串转换为分钟数"""
        hours, minutes = map(int, time_str.split(':'))
        return hours * 60 + minutes
    
    def _minutes_to_time(self, minutes: int) -> str:
        """将分钟数转换为时间字符串"""
        hours = minutes // 60
        mins = minutes % 60
        return f"{hours:02d}:{mins:02d}"
