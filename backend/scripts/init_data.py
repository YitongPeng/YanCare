"""
初始化数据脚本 - 创建预设的卡类型

运行方式：
cd backend
python -m scripts.init_data
"""
import asyncio
import sys
import os

# 添加项目根目录到路径
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from sqlalchemy import select
from app.database import async_session_maker, init_db
from app.models.card import CardType, ServiceType
from app.models.user import User, UserRole


# 预设的卡类型数据
CARD_TYPES = [
    {
        "name": "洗头卡",
        "service_type": ServiceType.WASH,
        "total_times": 50,
        "validity_days": None,  # 永久有效
        "price": 1000,
        "single_price": 60,
        "deduct_times": 1,
        "duration_minutes": 30,
        "notes": None,
    },
    {
        "name": "泡头卡",
        "service_type": ServiceType.SOAK,
        "total_times": 30,
        "validity_days": 182,  # 半年
        "price": 1800,
        "single_price": 128,
        "deduct_times": 1,
        "duration_minutes": 50,
        "notes": "泡头必洗头",
    },
    {
        "name": "尊享保养卡",
        "service_type": ServiceType.CARE,
        "total_times": None,  # 无限次
        "validity_days": 365,  # 1年
        "price": 13800,
        "single_price": 128,
        "deduct_times": 1,
        "duration_minutes": 50,
        "notes": "建议每日1次",
    },
    {
        "name": "固本保养卡",
        "service_type": ServiceType.CARE,
        "total_times": 60,
        "validity_days": 548,  # 1.5年
        "price": 5000,
        "single_price": 128,
        "deduct_times": 1,
        "duration_minutes": 50,
        "notes": "建议每周≥1次",
    },
    {
        "name": "深度保养卡",
        "service_type": ServiceType.CARE,
        "total_times": 100,
        "validity_days": 365,  # 1年
        "price": 6000,
        "single_price": 128,
        "deduct_times": 1,
        "duration_minutes": 50,
        "notes": "建议每周≥2次",
    },
    {
        "name": "强效保养卡",
        "service_type": ServiceType.CARE,
        "total_times": 180,
        "validity_days": 365,  # 1年
        "price": 9000,
        "single_price": 128,
        "deduct_times": 1,
        "duration_minutes": 50,
        "notes": None,
    },
    {
        "name": "综合卡（洗泡养）",
        "service_type": ServiceType.COMBO,
        "total_times": 100,
        "validity_days": 365,  # 1年
        "price": 6000,
        "single_price": 128,
        "deduct_times": 1,  # 洗头扣1次
        "duration_minutes": 50,
        "notes": "泡头和养发各扣2次",
    },
]


async def init_card_types():
    """初始化卡类型"""
    async with async_session_maker() as session:
        # 检查是否已有数据
        result = await session.execute(select(CardType))
        existing = result.scalars().all()
        
        if existing:
            print(f"卡类型已存在 ({len(existing)} 种)，跳过初始化")
            return
        
        # 创建卡类型
        for card_data in CARD_TYPES:
            card_type = CardType(**card_data)
            session.add(card_type)
        
        await session.commit()
        print(f"成功创建 {len(CARD_TYPES)} 种卡类型")


async def create_admin_user():
    """创建管理员用户（用于测试）"""
    async with async_session_maker() as session:
        # 检查是否已有管理员
        result = await session.execute(
            select(User).where(User.role == UserRole.ADMIN)
        )
        existing = result.scalar_one_or_none()
        
        if existing:
            print(f"管理员已存在: {existing.openid}")
            return
        
        # 创建管理员
        admin = User(
            openid="admin_test_openid",
            nickname="管理员",
            role=UserRole.ADMIN,
            real_name="系统管理员",
        )
        session.add(admin)
        await session.commit()
        print("成功创建管理员用户")


# 真实门店数据
STORES = [
    {
        "name": "燕斛堂养发（水岸新都店）",
        "address": "江阴市人民东路1023号佳兆业·水岸新都南区",
        "phone": "",  # 后续补充
        "latitude": 31.9105,
        "longitude": 120.2862,
        "opening_time": "08:15",
        "closing_time": "20:30",
        "description": "燕斛堂养发水岸新都店，专业养发护发服务",
    },
    {
        "name": "燕斛堂养发（阳光国际店）",
        "address": "江阴市先锋路98号",
        "phone": "",  # 后续补充
        "latitude": 31.9200,
        "longitude": 120.2750,
        "opening_time": "08:15",
        "closing_time": "20:30",
        "description": "燕斛堂养发阳光国际店，专业养发护发服务",
    },
]


async def init_stores():
    """初始化门店"""
    async with async_session_maker() as session:
        from app.models.store import Store
        
        # 检查是否已有数据
        result = await session.execute(select(Store))
        existing = result.scalars().all()
        
        if existing:
            print(f"门店已存在 ({len(existing)} 家)，跳过初始化")
            return
        
        # 创建门店
        for store_data in STORES:
            store = Store(**store_data)
            session.add(store)
        
        await session.commit()
        print(f"成功创建 {len(STORES)} 家门店")


async def create_test_staff():
    """创建测试员工"""
    async with async_session_maker() as session:
        # 检查是否已有员工
        result = await session.execute(
            select(User).where(User.role == UserRole.STAFF)
        )
        existing = result.scalars().all()
        
        if existing:
            print(f"员工已存在 ({len(existing)} 人)")
            return
        
        # 创建测试员工
        staff_list = [
            {"openid": "staff_001", "real_name": "小美", "introduction": "资深养发师，从业5年"},
            {"openid": "staff_002", "real_name": "小丽", "introduction": "专业技师，擅长头皮护理"},
        ]
        
        for staff_data in staff_list:
            staff = User(
                openid=staff_data["openid"],
                nickname=staff_data["real_name"],
                role=UserRole.STAFF,
                real_name=staff_data["real_name"],
                introduction=staff_data["introduction"],
            )
            session.add(staff)
        
        await session.commit()
        print(f"成功创建 {len(staff_list)} 名测试员工")


async def main():
    """主函数"""
    print("开始初始化数据...")
    
    # 初始化数据库表
    await init_db()
    print("数据库表创建完成")
    
    # 初始化卡类型
    await init_card_types()
    
    # 初始化门店
    await init_stores()
    
    # 创建管理员
    await create_admin_user()
    
    # 创建测试员工
    await create_test_staff()
    
    print("数据初始化完成！")


if __name__ == "__main__":
    asyncio.run(main())
