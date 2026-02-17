"""
认证路由 - 登录
"""
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.schemas.auth import WechatLoginRequest, NameLoginRequest, TokenResponse
from app.services.auth import AuthService

router = APIRouter(prefix="/auth", tags=["认证"])


@router.post("/name-login")
async def name_login(
    request: NameLoginRequest,
    db: AsyncSession = Depends(get_db)
):
    """
    名字登录
    
    1. 顾客输入名字即可登录，一个名字对应一个独立账号
    2. 员工需要输入名字 + 员工密码
    3. 后端验证并返回 JWT token
    """
    auth_service = AuthService(db)
    result = await auth_service.name_login(
        name=request.name,
        role=request.role,
        staff_password=request.staff_password
    )
    
    if not result:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="登录失败"
        )
    
    # 检查是否有错误（如密码错误）
    if isinstance(result, dict) and "error" in result:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=result["error"]
        )
    
    return result


@router.post("/wechat-login")
async def wechat_login(
    request: WechatLoginRequest,
    db: AsyncSession = Depends(get_db)
):
    """
    微信小程序登录（保留兼容）
    
    1. 前端调用 wx.login() 获取 code
    2. 选择角色（customer/staff），员工需要输入密码
    3. 后端验证并返回 JWT token
    """
    auth_service = AuthService(db)
    result = await auth_service.wechat_login(
        code=request.code,
        role=request.role,
        staff_password=request.staff_password,
        nickname=request.nickname,
        avatar_url=request.avatar_url
    )
    
    if not result:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="微信登录失败"
        )
    
    # 检查是否有错误（如密码错误）
    if isinstance(result, dict) and "error" in result:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=result["error"]
        )
    
    return result


@router.get("/me", response_model=dict)
async def get_current_user_info(
    current_user = Depends(AuthService.get_current_user)
):
    """获取当前用户信息"""
    return {
        "id": current_user.id,
        "openid": current_user.openid,
        "nickname": current_user.nickname,
        "phone": current_user.phone,
        "avatar_url": current_user.avatar_url,
        "role": current_user.role.value,
        "real_name": current_user.real_name,
    }
